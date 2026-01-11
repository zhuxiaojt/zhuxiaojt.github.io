# Zhuxiao Open Markdown Render User Guide

[简体中文](https://zhuxiaojt.github.io/docs/api/mdrender?zh-cn) | English

Special reminder: This document is translated by AI, and we are not responsible for the translated content.

## Basic Information

- API Address (iframe Embedding Address): `https://zhuxiaojt.github.io/api/md/mdrender.html`
- Communication Method: Browser-native `window.postMessage` for cross-page communication
- Supported Environments: Usable for both same-origin and cross-origin embedding
- Core Capabilities: Receive Markdown text for rendering, and receive CSS text for style injection

## 1. Create an iframe Container

Basic code for the parent page to embed the renderer; all attributes correspond to actual functional configurations:

```html
<iframe 
    id="mdRenderIframe"
    src="https://zhuxiaojt.github.io/api/md/mdrender.html"
    width="100%"
    height="800px"
    frameborder="0"
    allowtransparency="true"
></iframe>
```

### iframe Attribute Description

- `id`: Custom container identifier, used to retrieve the node via JS
- `src`: Fixed renderer address, cannot be modified
- `width/height`: Width and height settings, supporting percentage / pixel values
- `frameborder="0"`: Removes the default border
- `allowtransparency="true"`: Enables transparent background to show the parent page's background
- Initial State: Displays `Waiting...` after loading is complete

## 2. General Communication Rules

1. The parent page sends instruction objects via `iframe.contentWindow.postMessage(instructionObject, '*')`
2. The renderer has a built-in `window.addEventListener('message')` to listen for instructions
3. The `type` value of the instruction is strictly case-sensitive; no response will be returned if incorrect
4. Empty values or non-string parameters are ignored without error reporting
5. Sending duplicate instructions will overwrite the execution result of the previous one

## 3. Instruction 1: SetRenderText - Render Markdown Content

### Function

Receives a Markdown string, completes parsing and rendering; during the rendering process, it will first display the `Loading...

### Instruction Parameter Format

```javascript
{
    type: "SetRenderText",
    text: "Markdown format text"
}
```

### Parameter Description

- `type`: Fixed value `SetRenderText`
- `text`: String type, required, Markdown text content

### Calling Example

```javascript
const iframe = document.getElementById('mdRenderIframe');
const mdContent = `# Level 1 Heading
## Level 2 Heading
Normal text, supporting **bold**, *italic*, ~~strikethrough~~

### Lists
- Unordered list item
1. Ordered list item

### Code Block
\`\`\`javascript
let a = 1;
console.log(a);
\`\`\``;

iframe.contentWindow.postMessage({
    type: "SetRenderText",
    text: mdContent
}, '*');
```

### Supported Rendered Content

1. Basic Markdown Syntax: Headings, paragraphs, bold, italic, strikethrough, hyperlinks, lists, blockquotes, horizontal rules, inline code, code blocks
2. Formula Rendering: Inline formulas ( $formula$ ), block-level formulas ( $$formula$$ ), parsed based on KaTeX
3. Code Highlighting: Based on highlight.js; code blocks must be labeled with language identifiers

## 4. Instruction 2: injectStyle - Inject Custom Styles

### Function

Receives a CSS string, generates a style tag and makes it effective.

### Core Mechanism

Binds the style tag with a fixed ID `parent-inject-style`. When duplicate instructions are sent, the old tag is deleted first before creating a new one to avoid style duplication.

### Instruction Parameter Format

```javascript
{
    type: "injectStyle",
    css: "CSS style string"
}
```

### Parameter Description

- `type`: Fixed value `injectStyle`
- `css`: String type, required, standard CSS content

### List of Elements / Class Names for Style Injection

#### 1. Root Container and Basic Elements

```css
html {}
body {}
.markdown-render {} /* Outer container for rendered content */
```

#### 2. Natively Parsed Markdown Elements

```css
.markdown-render h1 {}
.markdown-render h2 {}
.markdown-render h3 {}
.markdown-render h4 {}
.markdown-render h5 {}
.markdown-render h6 {}
.markdown-render p {}
.markdown-render a {}
.markdown-render ul {}
.markdown-render ol {}
.markdown-render li {}
.markdown-render blockquote {}
.markdown-render hr {}
.markdown-render strong {}
.markdown-render em {}
.markdown-render del {}
.markdown-render code {} /* Inline code */
```

#### 3. Exclusive Elements for Code Highlighting

```css
.markdown-render pre {}     /* Outer container for code blocks */
.markdown-render pre code {}/* Code block content */
```

#### 4. Exclusive Elements for Formula Rendering

```css
.markdown-render .katex {}       /* Normal formula style */
.markdown-render .katex-error {} /* Style for formula parsing failure */
```

### Calling Example

```javascript
const iframe = document.getElementById('mdRenderIframe');
const customCss = `
.markdown-render {
    font-size: 16px;
    line-height: 1.8;
    color: #333;
    padding: 15px;
}
.markdown-render h1 {
    font-size: 22px;
    border-bottom: 1px solid #eee;
}
.markdown-render pre {
    background: #f8f8f8;
    padding: 12px;
    border-radius: 4px;
}
`;

iframe.contentWindow.postMessage({
    type: "injectStyle",
    css: customCss
}, '*');
```

## 3. Instruction 3: GetHTML - Get Rendered Content

### Function

After sending an instruction to the renderer, retrieve the content of the Markdown-rendered container, and return the result to the parent page through a specified event type.

### Instruction Parameter Format

```javascript
{
    type: "GetHTML",
    listenEventType: "Custom event type string"
}
```

### Parameter Description

- `type`: Fixed value `GetHTML`, used to trigger the content retrieval instruction
- `listenEventType`: String type, required, the event type identifier monitored by the parent page; the renderer will return results using this type; **Note**: There is a typo in the current code (needs to correct `msg.listenEvent.trim()` to `msg.listenEventType.trim()`, otherwise parameter validation will not take effect)

### Calling Example (Parent Page JS)

```javascript
const iframe = document.getElementById('mdRenderIframe');

// 1. The parent page first listens to the specified event (consistent with listenEventType)
window.addEventListener('message', function (e) {
    // Match the event type returned by the renderer
    if (e.data.type === 'renderContentReply') {
        console.log('Obtained rendered content:', e.data.html);
        // Process the obtained content here (e.g., store, display, etc.)
    }
});

// 2. Send the GetHTML instruction
iframe.contentWindow.postMessage({
    type: "GetHTML",
    listenEventType: "renderContentReply" // Consistent with the monitored event type
}, '*');
```

### Reply Format Description

After receiving the instruction, the renderer returns data in the following format to the parent page via `window.parent.postMessage`:

```javascript
{
    type: "Custom event type (i.e., the value of listenEventType)",
    html: "Text content inside the Markdown rendering container"
}
```

Note: The returned `html` field is actually the `textContent` property value of the rendering container (`#markdownRender`), i.e., plain text content without HTML tags.

## 5. Regular Calling Method: Inject Styles First, Then Render Content

```javascript
const iframe = document.getElementById('mdRenderIframe');
iframe.onload = function() {
    // Inject styles
    iframe.contentWindow.postMessage({
        type: "injectStyle",
        css: ".markdown-render { color: #333; font-size: 16px; }"
    }, '*');
    // Render content
    iframe.contentWindow.postMessage({
        type: "SetRenderText",
        text: "# Test Heading \n Test content $E=mc^2$"
    }, '*');
};
```

## 6. Direct Console Debugging of Instructions

1. Markdown rendering instruction

```javascript
postMessage({type:'SetRenderText',text:'# Test\nInline formula: $E=mc^2$\n```js\nconsole.log(1)\n```'}, '*');
```

1. Style injection instruction

```javascript
postMessage({type:'injectStyle',css:'.markdown-render{color:#666;padding:20px}'}, '*');
```

1. Restore initial state

```javascript
document.getElementById('markdownRender').innerHTML='<p>Waiting for rendering...</p>';
```

## 7. Notes

1. The `type` value of the instruction is strictly case-sensitive
2. If styles fail to take effect, add `!important` to force override
3. Due to JS's built-in escape rules, backslashes in hard-coded content must be written as double backslashes `\\` for escaping
4. Due to the special meaning of the backtick (\`) in JS, backticks in hard-coded content must be escaped with a backslash (\\\`)
5. Code blocks must be labeled with language identifiers for proper highlighting
6. The iframe's `src` address cannot be modified
7. Renderer resources use relative paths and are loaded based on their own domain name
8. Please ensure your device can stably access GitHub Pages
9. The GetHTML instruction must be called after Markdown content is rendered; otherwise, you may retrieve the `Loading...` text
10. The `listenEventType` parameter of the GetHTML instruction must strictly match the event type monitored by the parent page; otherwise, the returned result cannot be received correctly
11. The content returned by GetHTML does not include injected styles; if you need to display it on other pages, define an additional stylesheet
12. Please use absolute links for any links in the Markdown content
