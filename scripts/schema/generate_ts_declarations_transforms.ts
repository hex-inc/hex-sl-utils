import ts, { EmitHint, Identifier, Node } from "typescript";

/*
--------------------------------------------------------------------------------------------------------------------------------
Remove any instances of `oneOf:` from the JSON schema, as they are not supported by the TS converter
and can cause issues in the generated schema.
 */
export function removeUnsupportedConfigsFromJsonSchema(jsonSchema: any): any {
  function hasUnsupportedOneOf(jsonSchema: any): boolean {
    if (!jsonSchema.oneOf) return false;
    // inner refs imply that there is a discriminator, which _is_ supported by the TS converter
    if (jsonSchema.oneOf.every((item: any) => item.$ref)) return false;
    return true;
  }
  if (hasUnsupportedOneOf(jsonSchema)) delete jsonSchema.oneOf;
  for (const [defKey, def] of Object.entries(jsonSchema.$defs))
    if (hasUnsupportedOneOf(def)) delete jsonSchema.$defs[defKey].oneOf;
  return jsonSchema;
}

/*
--------------------------------------------------------------------------------------------------------------------------------
Remove any instances of `title:` from the JSON schema in cases where the properties title matches the key name.
This is done to simplify the generated TS declarations by omitting indirect types where unnecessary, such as `export type Cats = Cat[]`.
 */
export function removeRedundantPropertyTypeTitlesFromJsonSchema(
  jsonSchema: any,
  context: "properties" | { propertyKey: string } | null = null,
  definitionNames: Set<string> = new Set(Object.keys(jsonSchema.$defs ?? {})),
): any {
  const hasAtMostOneNonNullVariant = (variants: any[] | undefined) =>
    !variants || variants.filter((variant) => variant.type !== "null").length <= 1;

  if (Array.isArray(jsonSchema)) {
    return jsonSchema.map((i) =>
      removeRedundantPropertyTypeTitlesFromJsonSchema(i, null, definitionNames),
    );
  } else if (typeof jsonSchema === "object" && jsonSchema !== null) {
    const result: any = {};
    if (context && typeof context === "object" && "propertyKey" in context) {
      const normalizeName = (name: string) => name.toLowerCase().replaceAll("_", " ");
      if (
        jsonSchema.title &&
        normalizeName(jsonSchema.title) === normalizeName(context.propertyKey) &&
        (((!jsonSchema.anyOf || jsonSchema.anyOf.length <= 1) &&
          (!jsonSchema.oneOf || jsonSchema.oneOf.length <= 1)) ||
          (definitionNames.has(jsonSchema.title) &&
            hasAtMostOneNonNullVariant(jsonSchema.anyOf) &&
            hasAtMostOneNonNullVariant(jsonSchema.oneOf))) &&
        (!jsonSchema.enum || jsonSchema.enum.length <= 1)
      ) {
        return { ...jsonSchema, title: undefined };
      }
    } else {
      for (const [key, value] of Object.entries(jsonSchema)) {
        if (context === "properties") {
          result[key] = removeRedundantPropertyTypeTitlesFromJsonSchema(
            value,
            {
              propertyKey: key,
            },
            definitionNames,
          );
        } else if (key === "properties") {
          result[key] = removeRedundantPropertyTypeTitlesFromJsonSchema(
            value,
            "properties",
            definitionNames,
          );
        } else {
          result[key] = removeRedundantPropertyTypeTitlesFromJsonSchema(
            value,
            null,
            definitionNames,
          );
        }
      }
      return result;
    }
  }
  return jsonSchema;
}

/*
--------------------------------------------------------------------------------------------------------------------------------
Replace the trailing `[k: string]: unknown;` of types with `additionalProperties: true`
to instead allow `any` properties, which simplifies their consumption.
 */
export function replaceAdditionalPropertiesWithAny(code: string): string {
  return code.replaceAll("[k: string]: unknown", "[k: string]: any");
}

/**
--------------------------------------------------------------------------------------------------------------------------------
Adapted from https://github.com/bcherny/json-schema-to-typescript/issues/193
Fixes an issue in which the same type is used multiple times and results in
Type1, Type2, Type3, instead of a shared type definition.
 */

// FITS strings that do not end with digits (so duplicated types)
// AND strings that contain V1,V2,V3,... at the end (versioned API is considered as not duplicate)
const NON_DUPLICATED_IDENTIFIER_REGEXP = /\b(?!\w*\d+$)\w+\b|\b\w*V\d+\b/;

function isDuplicatedTypeIdentifier(typeIdentifier: Identifier): boolean {
  return !typeIdentifier.escapedText.toString().match(NON_DUPLICATED_IDENTIFIER_REGEXP);
}

function getNonDuplicatedIdentifierName(typeIdentifier: Identifier): string {
  // removes tail digits
  return typeIdentifier.escapedText.toString().replace(/[\d.]+$/, "");
}

export function removeDuplicateTSDeclarations(tsCode: string): string {
  const tsPrinter = ts.createPrinter(
    { newLine: ts.NewLineKind.LineFeed },
    {
      substituteNode: (_: EmitHint, node: Node): Node => {
        if (
          ts.isTypeReferenceNode(node) &&
          isDuplicatedTypeIdentifier(node.typeName as Identifier)
        ) {
          const originalIdentifierName = getNonDuplicatedIdentifierName(
            node.typeName as Identifier,
          );
          return ts.factory.createTypeReferenceNode(originalIdentifierName);
        }
        if (
          (ts.isInterfaceDeclaration(node) ||
            ts.isEnumDeclaration(node) ||
            ts.isTypeAliasDeclaration(node)) &&
          isDuplicatedTypeIdentifier(node.name as Identifier)
        ) {
          const declarationIsCleared = ts.factory.createIdentifier("");
          return declarationIsCleared;
        }
        return node;
      },
    },
  );

  const sourceFile = ts.createSourceFile(
    "",
    tsCode,
    ts.ScriptTarget.ESNext,
    false,
    ts.ScriptKind.TS,
  );

  const result = tsPrinter.printFile(sourceFile);

  return result;
}
