const fs = require("fs");
const path = require("path");

const siteRoot = path.resolve(__dirname, "..");
const labPagePath = path.join(siteRoot, "Projects", "ccie-sp-labs.html");
const labRoot = path.join(siteRoot, "Projects", "labs", "ccie-sp");
const fullConfigsPath = path.join(labRoot, "full-configs");
const featureNotesPath = path.join(labRoot, "feature-notes");

function countFiles(directory, extension = ".txt") {
  return fs
    .readdirSync(directory, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.toLowerCase().endsWith(extension))
    .length;
}

function countTopicChips(html) {
  const topicPanelMatch = html.match(/<article class="lab-panel topic-panel">[\s\S]*?<\/article>\s*<\/section>/);

  if (!topicPanelMatch) {
    throw new Error("Could not find the Lab Topics panel.");
  }

  const chipMatches = topicPanelMatch[0].match(/<span>[^<]+<\/span>/g);
  return chipMatches ? chipMatches.length : 0;
}

function formatCurrentMonthYear() {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    year: "numeric",
  }).format(new Date());
}

function replaceMetric(html, label, value) {
  const metricPattern = new RegExp(
    `(<div>\\s*<strong>)([^<]*)(<\\/strong>\\s*<span>${label}<\\/span>\\s*<\\/div>)`,
    "m"
  );

  if (!metricPattern.test(html)) {
    throw new Error(`Could not find metric: ${label}`);
  }

  return html.replace(metricPattern, `$1${value}$3`);
}

const html = fs.readFileSync(labPagePath, "utf8");
const metrics = {
  "Config files": countFiles(fullConfigsPath),
  "Feature notes": countFiles(featureNotesPath),
  "Core topics": countTopicChips(html),
  "Last update": formatCurrentMonthYear(),
};

let updatedHtml = html;

for (const [label, value] of Object.entries(metrics)) {
  updatedHtml = replaceMetric(updatedHtml, label, value);
}

fs.writeFileSync(labPagePath, updatedHtml, "utf8");

console.log("Updated CCIE-SP lab metrics:");
for (const [label, value] of Object.entries(metrics)) {
  console.log(`- ${label}: ${value}`);
}
