'use strict';

/**
 * A JSON Schema (draft 2020-12) validator for the keyword subset the governance
 * plan schema uses — nothing more.
 *
 * This repository carries no npm dependencies (no package.json), and the
 * governance compiler runs inside actions/github-script, which cannot install
 * one. So instead of pulling in ajv, plan consumers validate against
 * ops/schemas/repo-governance-plan.schema.json with this module.
 *
 * It fails closed: a schema that uses a keyword outside the supported set is
 * rejected when compiled, so a later schema edit cannot silently widen what
 * "valid" means because this validator ignored the new keyword.
 *
 * Supported: type, const, enum, pattern, minLength, not, required, properties,
 * additionalProperties (boolean false only), items, uniqueItems, minItems,
 * $ref (local "#/$defs/<name>" only). Annotations ($schema, $id, $defs, title,
 * description) are accepted and ignored.
 */

const ANNOTATIONS = new Set(['$schema', '$id', '$defs', 'title', 'description']);
const ASSERTIONS = new Set([
  'type',
  'const',
  'enum',
  'pattern',
  'minLength',
  'not',
  'required',
  'properties',
  'additionalProperties',
  'items',
  'uniqueItems',
  'minItems',
  '$ref',
]);

function typeOf(value) {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  if (Number.isInteger(value)) return 'integer';
  return typeof value;
}

function matchesType(value, type) {
  const actual = typeOf(value);
  if (type === 'number') return actual === 'number' || actual === 'integer';
  return actual === type;
}

// Structural equality for const / enum / uniqueItems.
function sameJson(a, b) {
  return JSON.stringify(canonicalize(a)) === JSON.stringify(canonicalize(b));
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === 'object') {
    const out = {};
    for (const k of Object.keys(value).sort()) out[k] = canonicalize(value[k]);
    return out;
  }
  return value;
}

function checkKeywords(node, where) {
  if (typeof node === 'boolean') return;
  if (!node || typeof node !== 'object') throw new Error(`schema node at ${where} is not an object`);
  for (const key of Object.keys(node)) {
    if (!ANNOTATIONS.has(key) && !ASSERTIONS.has(key)) {
      throw new Error(`unsupported JSON Schema keyword "${key}" at ${where}`);
    }
  }
  if ('additionalProperties' in node && node.additionalProperties !== false) {
    throw new Error(`only "additionalProperties": false is supported (at ${where})`);
  }
  if ('$ref' in node && !/^#\/\$defs\/[A-Za-z0-9_]+$/.test(node.$ref)) {
    throw new Error(`only local "#/$defs/<name>" refs are supported (at ${where})`);
  }
  for (const [name, sub] of Object.entries(node.properties || {})) checkKeywords(sub, `${where}/properties/${name}`);
  for (const [name, sub] of Object.entries(node.$defs || {})) checkKeywords(sub, `${where}/$defs/${name}`);
  if (node.items) checkKeywords(node.items, `${where}/items`);
  if (node.not) checkKeywords(node.not, `${where}/not`);
}

/**
 * @param {object} schema
 * @returns {(value: unknown) => string[]} validate function returning errors
 */
function compileSchema(schema) {
  checkKeywords(schema, '#');
  const defs = schema.$defs || {};

  function validate(value, node, path, errors) {
    if (node === true) return;
    if (node === false) {
      errors.push(`${path}: no value is allowed here`);
      return;
    }
    if (node.$ref) {
      const target = defs[node.$ref.slice('#/$defs/'.length)];
      if (!target) throw new Error(`unresolved $ref ${node.$ref}`);
      validate(value, target, path, errors);
    }
    if (node.type && !matchesType(value, node.type)) {
      errors.push(`${path}: expected ${node.type}, got ${typeOf(value)}`);
      return;
    }
    if ('const' in node && !sameJson(value, node.const)) {
      errors.push(`${path}: must equal ${JSON.stringify(node.const)}`);
    }
    if (node.enum && !node.enum.some((e) => sameJson(value, e))) {
      errors.push(`${path}: must be one of ${JSON.stringify(node.enum)}`);
    }
    if (typeof value === 'string') {
      if (node.minLength != null && [...value].length < node.minLength) {
        errors.push(`${path}: shorter than ${node.minLength}`);
      }
      if (node.pattern && !new RegExp(node.pattern, 'u').test(value)) {
        errors.push(`${path}: does not match ${node.pattern}`);
      }
    }
    if (node.not) {
      const sub = [];
      validate(value, node.not, path, sub);
      if (!sub.length) errors.push(`${path}: matches a disallowed form`);
    }
    if (Array.isArray(value)) {
      if (node.minItems != null && value.length < node.minItems) {
        errors.push(`${path}: fewer than ${node.minItems} items`);
      }
      if (node.uniqueItems) {
        for (let i = 0; i < value.length; i++) {
          for (let j = i + 1; j < value.length; j++) {
            if (sameJson(value[i], value[j])) errors.push(`${path}: items ${i} and ${j} are duplicates`);
          }
        }
      }
      if (node.items) value.forEach((item, i) => { validate(item, node.items, `${path}[${i}]`, errors); });
    }
    if (typeOf(value) === 'object') {
      for (const key of node.required || []) {
        if (!Object.hasOwn(value, key)) errors.push(`${path}: missing required "${key}"`);
      }
      const props = node.properties || {};
      for (const [key, sub] of Object.entries(value)) {
        if (Object.hasOwn(props, key)) {
          validate(sub, props[key], `${path}.${key}`, errors);
        } else if (node.additionalProperties === false) {
          errors.push(`${path}: unexpected property "${key}"`);
        }
      }
    }
  }

  return (value) => {
    const errors = [];
    validate(value, schema, '$', errors);
    return errors;
  };
}

module.exports = { compileSchema };
