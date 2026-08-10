import fs from "fs";
import path from "path";
import { format as prettierFormat } from "prettier";
import { compile as jsonSchemaToTs } from "json-schema-to-typescript";
import {
  removeDuplicateTSDeclarations,
  removeRedundantPropertyTypeTitlesFromJsonSchema,
  removeUnsupportedConfigsFromJsonSchema,
  replaceAdditionalPropertiesWithAny,
} from "./generate_ts_declarations_transforms";

const SCHEMA_FILES_PATH = path.resolve(
  __dirname,
  "../../packages/hex-sl-utils/src/hex_sl_utils/schema_files",
);
const JSON_SCHEMAS_PATH = path.join(SCHEMA_FILES_PATH, "jsonschema");
const TS_D_PATH = path.join(SCHEMA_FILES_PATH, "ts");
const TARGETS = ["hex_resource_schema"];

function main() {
  for (const target of TARGETS) {
    const jsonSchemaPath = path.resolve(JSON_SCHEMAS_PATH, `${target}.json`);
    let jsonSchema = JSON.parse(fs.readFileSync(jsonSchemaPath, "utf8"));
    jsonSchema = removeUnsupportedConfigsFromJsonSchema(jsonSchema);
    jsonSchema = removeRedundantPropertyTypeTitlesFromJsonSchema(jsonSchema);
    void jsonSchemaToTs(jsonSchema, "Dataset", { additionalProperties: false })
      .then(replaceAdditionalPropertiesWithAny)
      .then(removeDuplicateTSDeclarations)
      .then((s) => prettierFormat(s, { parser: "typescript" }))
      .then((tsDeclarations) => {
        fs.writeFileSync(path.resolve(TS_D_PATH, `${target}.d.ts`), tsDeclarations, "utf8");
      });
  }
}

main();
