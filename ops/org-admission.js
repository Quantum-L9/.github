"use strict";

/**
 * The `admit` job of auto-seed-new-repo.yml (ADR-040): one organization
 * repository becomes one reviewable registry-admission pull request.
 *
 * Since v3.43.0 semantics/repository_registry.yaml is organization-complete:
 * every repository the organization hosts must be registered. The entry and
 * its release record are rendered by ops/register-org-repository.py; this
 * module decides whether the target is this path's to admit, and opens or
 * updates the PR. It never merges: the owner's merge of that exact entry is
 * the admission decision.
 *
 * A factory-born repository (it carries .l9/birth-receipt.json) is the birth
 * path's to register (ADR-039, repo-birth-bootstrap.yml `register`), and an
 * archived one is admitted by hand with lifecycle retired, so both are
 * skipped here rather than proposed twice or wrongly.
 */

const ORG = "Quantum-L9";
const BRANCH_PREFIX = "org-registry/";
const BIRTH_RECEIPT = ".l9/birth-receipt.json";
const REPO_NAME = /^[A-Za-z0-9._-]{1,100}$/;

const subjectFor = (name) =>
	`chore(registry): admit organization repository ${ORG}/${name}`;

/**
 * Decide whether `name` is this path's to admit.
 *
 * @param {{github: object, name: string}} o
 * @returns {Promise<{action: "admit"|"skip", reason: string|null,
 *   githubId?: number, defaultBranch?: string}>}
 *   Throws on anything that is not a clear answer (an unreadable repository,
 *   or a receipt probe that is neither present nor 404): the job fails rather
 *   than proposing an entry it cannot justify.
 */
async function classifyAdmissionTarget({ github, name }) {
	if (!REPO_NAME.test(String(name)))
		throw new Error(`invalid repository name ${JSON.stringify(name)}`);
	if (name === ".github")
		return { action: "skip", reason: ".github is registered as dot-github" };
	const { data: repo } = await github.rest.repos.get({
		owner: ORG,
		repo: name,
	});
	if (repo.archived === true) {
		return {
			action: "skip",
			reason: `${ORG}/${name} is archived: admit it by hand with lifecycle retired`,
		};
	}
	if (!Number.isInteger(repo.id) || repo.id <= 0)
		throw new Error(`${ORG}/${name}: GitHub returned no repository id`);
	try {
		await github.rest.repos.getContent({
			owner: ORG,
			repo: name,
			path: BIRTH_RECEIPT,
			ref: repo.default_branch,
		});
		return {
			action: "skip",
			reason: `${ORG}/${name} is factory-born (${BIRTH_RECEIPT}); repo-birth-bootstrap.yml registers it (ADR-039)`,
		};
	} catch (e) {
		// 404: no receipt. 409: an empty repository, which cannot carry one.
		if (e.status !== 404 && e.status !== 409) throw e;
	}
	return {
		action: "admit",
		reason: null,
		githubId: repo.id,
		defaultBranch: repo.default_branch,
	};
}

/**
 * Open or update the admission PR for an `apply` result of
 * ops/register-org-repository.py. Mirrors the birth registrar's branch
 * discipline: a branch carrying any commit this job did not author is left
 * alone, a stale branch is advanced by a merge commit over the current base
 * (never force-moved), and an up-to-date branch is not rewritten.
 *
 * @param {{github: object, core: object, context: object, result: object,
 *   readFile: (p: string) => string, baseSha: string, base: string}} o
 * @returns {Promise<{status: string, url?: string}>}
 */
async function openAdmissionPr({
	github,
	core,
	context,
	result,
	readFile,
	baseSha,
	base,
}) {
	const { owner, repo } = context.repo;
	const entry = result.entry;
	const target = entry.coordinate.repository;
	if (result.status === "present") {
		core.notice(
			`${ORG}/${target} is already registered on ${base}; nothing to do`,
		);
		return { status: "present" };
	}
	if (result.status !== "added" || !result.changed_paths?.length) {
		core.setFailed(
			`unexpected admission result ${JSON.stringify(result.status)}`,
		);
		return { status: "failed" };
	}
	const branch = `${BRANCH_PREFIX}${target}`;
	const subject = subjectFor(target);
	const baseCommit = await github.rest.git.getCommit({
		owner,
		repo,
		commit_sha: baseSha,
	});

	let branchSha = null;
	try {
		const ref = await github.rest.git.getRef({
			owner,
			repo,
			ref: `heads/${branch}`,
		});
		branchSha = ref.data.object.sha;
	} catch (e) {
		if (e.status !== 404) throw e;
	}
	if (branchSha) {
		const cmp = await github.rest.repos.compareCommitsWithBasehead({
			owner,
			repo,
			basehead: `${baseSha}...${branchSha}`,
		});
		const foreign = cmp.data.commits.filter(
			(c) => !c.commit.message.startsWith(subject),
		);
		if (foreign.length) {
			core.setFailed(
				`${branch} carries ${foreign.length} commit(s) the admission job did not author; ` +
					"refusing to rewrite it — resolve that PR by hand",
			);
			return { status: "foreign" };
		}
	}

	const tree = await github.rest.git.createTree({
		owner,
		repo,
		base_tree: baseCommit.data.tree.sha,
		tree: result.changed_paths.map((path) => ({
			path,
			mode: "100644",
			type: "blob",
			content: readFile(path),
		})),
	});
	let unchanged = false;
	if (branchSha) {
		const head = await github.rest.git.getCommit({
			owner,
			repo,
			commit_sha: branchSha,
		});
		unchanged = head.data.tree.sha === tree.data.sha;
	}
	const marker = entry.organization_admission;
	if (unchanged) {
		core.notice(`${branch} already carries this admission`);
	} else {
		const message = [
			subject,
			"",
			`Entry ${entry.id} (${entry.class_ref}, lifecycle ${entry.lifecycle}), release ${result.release},`,
			`GitHub repository id ${marker.github_repository_id} observed ${marker.observed_at} (ADR-040).`,
		].join("\n");
		const commit = await github.rest.git.createCommit({
			owner,
			repo,
			message,
			tree: tree.data.sha,
			parents: branchSha ? [branchSha, baseSha] : [baseSha],
		});
		if (branchSha) {
			await github.rest.git.updateRef({
				owner,
				repo,
				ref: `heads/${branch}`,
				sha: commit.data.sha,
				force: false,
			});
		} else {
			await github.rest.git.createRef({
				owner,
				repo,
				ref: `refs/heads/${branch}`,
				sha: commit.data.sha,
			});
		}
	}

	const body = [
		`Admits \`${ORG}/${target}\` to \`semantics/repository_registry.yaml\` (ADR-040, organization completeness).`,
		"",
		"| Field | Value |",
		"| --- | --- |",
		`| id | \`${entry.id}\` |`,
		`| class_ref | \`${entry.class_ref}\` |`,
		`| lifecycle | \`${entry.lifecycle}\` |`,
		...Object.entries(marker).map(
			([k, v]) => `| organization_admission.${k} | \`${v}\` |`,
		),
		`| release record | \`docs/semantic-foundation/${result.release}/\` |`,
		"",
		"The id is the folding of the repository name and the class is the single current admitted",
		"RepositoryClass; nothing was typed (`ops/register-org-repository.py`). The semantic validator",
		"passed on this tree before the PR was opened.",
		"",
		"Registration is organization membership only: no ProductKind, no Node, no constellation",
		"participation. Merging this exact entry is the admission decision. This workflow never merges.",
		"",
		"## Problem",
		"",
		`\`${ORG}/${target}\` is hosted in the organization but not registered, which the organization-completeness`,
		"rule (ADR-040) forbids; this adds exactly its entry.",
		"",
		"## Risk",
		"",
		"- [x] Low — one additive registry entry plus the release record the semantic validator requires",
		"- [ ] Medium",
		"- [ ] High",
		"",
		"## Evidence",
		"",
		`- Admission run: ${context.serverUrl}/${owner}/${repo}/actions/runs/${context.runId}`,
		"- `ops/register-org-repository.py` ran the semantic validator on this tree before this PR was opened.",
	].join("\n");
	const open = await github.rest.pulls.list({
		owner,
		repo,
		state: "open",
		head: `${owner}:${branch}`,
		base,
	});
	if (open.data.length) {
		await github.rest.pulls.update({
			owner,
			repo,
			pull_number: open.data[0].number,
			body,
		});
		core.notice(`updated ${open.data[0].html_url}`);
		return { status: "updated", url: open.data[0].html_url };
	}
	const pr = await github.rest.pulls.create({
		owner,
		repo,
		head: branch,
		base,
		title: subject,
		body,
	});
	core.notice(`opened ${pr.data.html_url}`);
	return { status: "opened", url: pr.data.html_url };
}

module.exports = {
	ORG,
	BRANCH_PREFIX,
	BIRTH_RECEIPT,
	subjectFor,
	classifyAdmissionTarget,
	openAdmissionPr,
};
