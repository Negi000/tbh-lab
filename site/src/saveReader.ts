export type LocaleCode = string;
export type Localized = Partial<Record<string, string>>;

export type SaveOwnedItem = {
  itemKey: number;
  quantity: number;
  uniqueIds: string[];
  sources: Record<"inventory" | "stash" | "tradingStash" | "equipped", number>;
};

export type SaveHeroState = {
  heroKey: number;
  level: number;
  unlocked: boolean;
  equippedItemIds: string[];
  equippedSkillKeys: number[];
};

export type SavePetState = {
  petKey: number;
  unlocked: boolean;
  viewed: boolean;
};

export type SaveStageRoute = {
  stageKey: number;
  difficulty: "NORMAL" | "NIGHTMARE" | "HELL" | "TORMENT" | "";
  difficultyLabel: Localized;
  act: number;
  stageNo: number;
  label: Localized;
};

export type SaveSnapshot = {
  fileName: string;
  readAt: string;
  version: string;
  playTimeSeconds: number;
  gold: number;
  totalClears: number;
  currentStage: SaveStageRoute | null;
  maxCompletedStage: SaveStageRoute | null;
  currentStageWave: number;
  arrangedHeroKeys: number[];
  arrangedPetKey: number | null;
  heroes: SaveHeroState[];
  pets: SavePetState[];
  runeLevels: Record<string, number>;
  ownedItems: SaveOwnedItem[];
  occupiedSlots: {
    inventory: number;
    stash: number;
    tradingStash: number;
    equipped: number;
  };
  aggregate: Array<{ type: number; subKey: number; value: number }>;
};

const ES3_PASSWORD = "emuMqG3bLYJ938ZDCfieWJ";
const GOLD_KEY = 100001;
const TOTAL_CLEARS_TYPE = 15;
const TOTAL_CLEARS_SUBKEY = 0;

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asList(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.map(asRecord).filter((row) => Object.keys(row).length > 0) : [];
}

function numberValue(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
}

function stringValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

function boolValue(value: unknown): boolean {
  return value === true || value === "true" || value === 1;
}

function stripPkcs7(bytes: Uint8Array): Uint8Array {
  const pad = bytes[bytes.length - 1];
  if (pad < 1 || pad > 16 || pad > bytes.length) {
    return bytes;
  }
  for (let index = bytes.length - pad; index < bytes.length; index += 1) {
    if (bytes[index] !== pad) {
      return bytes;
    }
  }
  return bytes.slice(0, bytes.length - pad);
}

async function gzipDecompress(bytes: Uint8Array): Promise<Uint8Array> {
  if (typeof DecompressionStream === "undefined") {
    throw new Error("gzip decompression is not available in this browser");
  }
  const body = new ArrayBuffer(bytes.byteLength);
  new Uint8Array(body).set(bytes);
  const stream = new Blob([body]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

async function decryptEs3(buffer: ArrayBuffer): Promise<Uint8Array> {
  const blob = new Uint8Array(buffer);
  if (blob.length < 32) {
    throw new Error("save file is too small");
  }
  const iv = blob.slice(0, 16);
  const cipherLength = Math.floor((blob.length - 16) / 16) * 16;
  const cipherText = blob.slice(16, 16 + cipherLength);
  const passwordBytes = new TextEncoder().encode(ES3_PASSWORD);
  const keyMaterial = await crypto.subtle.importKey("raw", passwordBytes, "PBKDF2", false, ["deriveKey"]);
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: iv, iterations: 100, hash: "SHA-1" },
    keyMaterial,
    { name: "AES-CBC", length: 128 },
    false,
    ["decrypt"],
  );
  const decrypted = new Uint8Array(await crypto.subtle.decrypt({ name: "AES-CBC", iv }, key, cipherText));
  const unpadded = stripPkcs7(decrypted);
  if (unpadded[0] === 0x1f && unpadded[1] === 0x8b) {
    return gzipDecompress(unpadded);
  }
  return unpadded;
}

function decodeStage(stageKey: number): SaveStageRoute | null {
  if (!Number.isFinite(stageKey) || stageKey <= 0) {
    return null;
  }
  const difficultyCode = Math.floor(stageKey / 1000);
  const act = Math.floor((stageKey % 1000) / 100);
  const stageNo = stageKey % 100;
  const difficulties: Record<number, { id: SaveStageRoute["difficulty"]; ja: string; en: string }> = {
    1: { id: "NORMAL", ja: "ノーマル", en: "Normal" },
    2: { id: "NIGHTMARE", ja: "ナイトメア", en: "Nightmare" },
    3: { id: "HELL", ja: "ヘル", en: "Hell" },
    4: { id: "TORMENT", ja: "トーメント", en: "Torment" },
  };
  const difficulty = difficulties[difficultyCode] ?? { id: "", ja: "", en: "" };
  return {
    stageKey,
    difficulty: difficulty.id,
    difficultyLabel: { ja: difficulty.ja, en: difficulty.en },
    act,
    stageNo,
    label: { ja: `${difficulty.ja} ${act}-${stageNo}`.trim(), en: `${difficulty.en} ${act}-${stageNo}`.trim() },
  };
}

function currencyAmount(rows: Record<string, unknown>[], key: number): number {
  const row = rows.find((entry) => numberValue(entry.Key) === key);
  return numberValue(row?.Quantity);
}

function aggregateAmount(rows: Record<string, unknown>[], type: number, subKey: number): number {
  const row = rows.find((entry) => numberValue(entry.Type) === type && numberValue(entry.SubKey) === subKey);
  return numberValue(row?.Value);
}

function slotUniqueId(row: Record<string, unknown>): string {
  const value = row.ItemUniqueId ?? row.itemUniqueId ?? row.UniqueId;
  const text = stringValue(value);
  return text === "0" ? "" : text;
}

function itemUniqueId(row: Record<string, unknown>): string {
  return stringValue(row.UniqueId ?? row.ItemUniqueId ?? row.uniqueId);
}

function addOwned(
  owned: Map<number, SaveOwnedItem>,
  itemKey: number,
  uniqueId: string,
  source: keyof SaveOwnedItem["sources"],
) {
  if (!itemKey || !uniqueId) {
    return;
  }
  const current =
    owned.get(itemKey) ??
    ({
      itemKey,
      quantity: 0,
      uniqueIds: [],
      sources: { inventory: 0, stash: 0, tradingStash: 0, equipped: 0 },
    } satisfies SaveOwnedItem);
  current.quantity += 1;
  current.sources[source] += 1;
  current.uniqueIds.push(uniqueId);
  owned.set(itemKey, current);
}

function collectOwnedItems(playerSave: Record<string, unknown>, heroes: SaveHeroState[]) {
  const itemRows = asList(playerSave.itemSaveDatas);
  const itemsByUniqueId = new Map<string, Record<string, unknown>>();
  for (const item of itemRows) {
    const uniqueId = itemUniqueId(item);
    if (uniqueId) {
      itemsByUniqueId.set(uniqueId, item);
    }
  }

  const owned = new Map<number, SaveOwnedItem>();
  const occupiedSlots = { inventory: 0, stash: 0, tradingStash: 0, equipped: 0 };
  const collectSlots = (key: "inventorySaveDatas" | "stashSaveDatas" | "tradingStashSaveDatas", source: keyof SaveOwnedItem["sources"]) => {
    for (const slot of asList(playerSave[key])) {
      const uniqueId = slotUniqueId(slot);
      if (!uniqueId) {
        continue;
      }
      occupiedSlots[source] += 1;
      const item = itemsByUniqueId.get(uniqueId);
      addOwned(owned, numberValue(item?.ItemKey), uniqueId, source);
    }
  };

  collectSlots("inventorySaveDatas", "inventory");
  collectSlots("stashSaveDatas", "stash");
  collectSlots("tradingStashSaveDatas", "tradingStash");
  for (const hero of heroes) {
    for (const uniqueId of hero.equippedItemIds) {
      if (!uniqueId) {
        continue;
      }
      occupiedSlots.equipped += 1;
      const item = itemsByUniqueId.get(uniqueId);
      addOwned(owned, numberValue(item?.ItemKey), uniqueId, "equipped");
    }
  }
  return { ownedItems: Array.from(owned.values()).sort((a, b) => b.quantity - a.quantity), occupiedSlots };
}

export async function readTaskbarHeroSave(file: File): Promise<SaveSnapshot> {
  const plain = await decryptEs3(await file.arrayBuffer());
  const top = asRecord(JSON.parse(new TextDecoder().decode(plain)));
  const playerSaveData = asRecord(top.PlayerSaveData);
  const value = playerSaveData.value;
  const playerSave = typeof value === "string" ? asRecord(JSON.parse(value)) : asRecord(value || top);
  const common = asRecord(playerSave.commonSaveData);
  const currencyRows = asList(playerSave.currenySaveDatas);
  const aggregateRows = asList(playerSave.aggregateSaveDatas);
  const heroes = asList(playerSave.heroSaveDatas).map((hero) => ({
    heroKey: numberValue(hero.heroKey ?? hero.HeroKey),
    level: numberValue(hero.HeroLevel),
    unlocked: boolValue(hero.IsUnLock ?? hero.IsUnlock),
    equippedItemIds: Array.isArray(hero.equippedItemIds) ? hero.equippedItemIds.map(stringValue).filter((id) => id && id !== "0") : [],
    equippedSkillKeys: Array.isArray(hero.equippedSKillKey) ? hero.equippedSKillKey.map((skill) => numberValue(skill)).filter(Boolean) : [],
  }));
  const { ownedItems, occupiedSlots } = collectOwnedItems(playerSave, heroes);
  const runeLevels = Object.fromEntries(
    asList(playerSave.RuneSaveData)
      .map((rune) => [stringValue(rune.RuneKey), numberValue(rune.Level)] as const)
      .filter(([key]) => key),
  );
  const pets = asList(playerSave.PetSaveData).map((pet) => ({
    petKey: numberValue(pet.PetKey),
    unlocked: boolValue(pet.IsUnlock ?? pet.IsUnlocked),
    viewed: boolValue(pet.IsViewed),
  }));

  return {
    fileName: file.name,
    readAt: new Date().toISOString(),
    version: stringValue(common.version),
    playTimeSeconds: numberValue(common.playTime),
    gold: currencyAmount(currencyRows, GOLD_KEY),
    totalClears: aggregateAmount(aggregateRows, TOTAL_CLEARS_TYPE, TOTAL_CLEARS_SUBKEY),
    currentStage: decodeStage(numberValue(common.currentStageKey)),
    maxCompletedStage: decodeStage(numberValue(common.maxCompletedStage)),
    currentStageWave: numberValue(common.currentStageWave),
    arrangedHeroKeys: Array.isArray(common.arrangedHeroKey) ? common.arrangedHeroKey.map((key) => numberValue(key)).filter(Boolean) : [],
    arrangedPetKey: numberValue(common.ArrangedPetKey) || null,
    heroes,
    pets,
    runeLevels,
    ownedItems,
    occupiedSlots,
    aggregate: aggregateRows
      .map((row) => ({ type: numberValue(row.Type), subKey: numberValue(row.SubKey), value: numberValue(row.Value) }))
      .filter((row) => row.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, 80),
  };
}
