export function delay(ms = 350) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
