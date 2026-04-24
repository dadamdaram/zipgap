const fs = require('fs');
const html = fs.readFileSync('frontend/index.html', 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (scriptMatch) {
  try {
    new Function(scriptMatch[1]);
    console.log("JS Syntax OK");
  } catch(e) {
    console.error("JS Syntax Error:", e);
  }
} else {
  console.log("No script tag found");
}
