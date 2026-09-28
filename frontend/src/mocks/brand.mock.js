import { delay } from "./delay";
import brandData from "./data/brand.json";

let brand = { ...brandData, target_audience: { ...brandData.target_audience } };

export async function getBrand() {
  await delay();
  return JSON.parse(JSON.stringify(brand));
}

export async function updateBrand(payload) {
  await delay();
  brand = { ...brand, ...payload, id: brand.id };
  return { id: brand.id };
}
