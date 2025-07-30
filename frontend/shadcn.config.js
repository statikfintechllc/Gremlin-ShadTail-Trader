/** @type {import('@shadcn/ui').Config} */
module.exports = {
  style: "default",
  rsc: false,
  tsx: true,
  tailwind: {
    config: "tailwind.config.cjs",
    css: "src/styles/globals.css",
    baseColor: "slate",
    cssVariables: true,
    prefix: "",
  },
  aliases: {
    components: "src/components",
    utils: "src/utils",
    ui: "src/components/ui",
  },
  components: [
    "button", 
    "card", 
    "tabs", 
    "input", 
    "table", 
    "scroll-area",
    "sheet",
    "dialog",
    "select"
  ],
  output: "src/components/ui",
}

