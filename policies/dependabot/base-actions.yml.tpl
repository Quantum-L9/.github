  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
      day: monday
    open-pull-requests-limit: 2
    commit-message:
      prefix: "chore(deps)"
    cooldown:
      default-days: 7
    ignore:
      - dependency-name: "Quantum-L9/.github*"
      - dependency-name: "Quantum-L9/l9-ci-core*"
      - dependency-name: "Quantum-L9/l9-ci-sdk*"
    groups:
      actions-minor-patch:
        patterns: ["*"]
        update-types: ["minor", "patch"]
