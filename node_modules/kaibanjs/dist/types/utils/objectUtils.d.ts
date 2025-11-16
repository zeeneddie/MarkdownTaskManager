/**
 * Gets the value at path of object. If the resolved value is undefined,
 * returns the defaultValue.
 */
export declare function oget<T>(obj: Record<string, unknown>, path: string, defaultValue?: T): T | undefined;
/**
 * Sets the value at path of object. If a portion of path doesn't exist, it's created.
 * Arrays are created for missing index properties while objects are created for all
 * other missing properties.
 */
export declare function oset(obj: Record<string, unknown>, path: string, value: unknown): void;
export declare function isEmpty(obj: Record<string, unknown> | undefined): boolean;
