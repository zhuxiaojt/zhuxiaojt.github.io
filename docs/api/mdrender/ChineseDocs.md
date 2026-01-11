# Zhuxiao Open Markdown Render 使用说明

简体中文 | [English](https://zhuxiaojt.github.io/docs/api/mdrender?en-us)

## 基础信息

- API 地址 (iframe 嵌入地址)：`https://zhuxiaojt.github.io/api/md/mdrender.html`
- 通信方式：浏览器原生 `window.postMessage` 页面通信
- 支持环境：同源 / 跨域嵌入均可使用
- 核心能力：接收 markdown 文本渲染、接收 css 文本注入样式

## 一、创建 iframe 容器

父页面嵌入渲染器的基础代码，所有属性均为实际功能配置

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

### iframe 属性说明

- `id`：自定义容器标识，用于 JS 获取节点
- `src`：固定渲染器地址，不可修改
- `width/height`：宽高设置，支持百分比 / 像素值
- `frameborder="0"`：移除默认边框
- `allowtransparency="true"`：开启透明背景，透出父页面背景
- 初始状态：加载完成后显示 `<p>Waiting...</p>`

## 二、通用通信规则

1. 父页面通过 `iframe.contentWindow.postMessage(指令对象, '*')` 发送指令
2. 渲染器内置 `window.addEventListener('message')` 监听指令
3. 指令 `type` 值严格区分大小写，错误则无响应
4. 空值 / 非字符串参数会被忽略，无报错
5. 重复发送指令会覆盖之前的执行结果

## 三、指令 1：SetRenderText - 渲染 Markdown 内容

### 功能

接收 markdown 字符串，完成解析与渲染；渲染过程中会先显示 `<p>Loading...</p>` 加载状态，渲染完成后替换为最终内容

### 指令参数格式

```javascript
{
    type: "SetRenderText",
    text: "markdown格式文本"
}
```

### 参数说明

- `type`：固定值 `SetRenderText`
- `text`：字符串类型，必填，markdown 文本内容

### 调用示例

```javascript
const iframe = document.getElementById('mdRenderIframe');
const mdContent = `# 一级标题
## 二级标题
普通文本，支持**粗体**、*斜体*、~~删除线~~

### 列表
- 无序列表项
1. 有序列表项

### 代码块
\`\`\`javascript
let a = 1;
console.log(a);
\`\`\`

### 公式
行内公式：$E=mc^2$
块级公式：
$$
\\sum_{i=1}^n i = \\frac{n(n+1)}{2}
$$

> 引用文本
---`;

iframe.contentWindow.postMessage({
    type: "SetRenderText",
    text: mdContent
}, '*');
```

### 支持的渲染内容

1. Markdown 基础语法：标题、段落、粗体、斜体、删除线、超链接、列表、引用、分割线、行内代码、代码块

2. 公式渲染：行内公式（ $公式$ ）、块级公式（ $公式$ ），基于 KaTeX 解析

3. 代码高亮：基于 highlight.js，代码块需标注语言标识

## 四、指令 2：injectStyle - 注入自定义样式

### 功能

接收 CSS 字符串，生成样式标签并生效

### 核心机制

通过固定 ID `parent-inject-style` 绑定样式标签，重复发送指令时先删除旧标签，再创建新标签，避免样式重复

### 指令参数格式

```javascript
{
    type: "injectStyle",
    css: "css样式字符串"
}
```

### 参数说明

- `type`：固定值 `injectStyle`
- `css`：字符串类型，必填，标准 CSS 内容

### 可注入样式的元素 / 类名清单

#### 1. 根容器与基础元素

```css
html {}
body {}
.markdown-render {} /* 渲染内容外层容器 */
```

#### 2. Markdown 原生解析元素

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
.markdown-render code {} /* 行内代码 */
```

#### 3. 代码高亮专属元素

```css
.markdown-render pre {}     /* 代码块外层容器 */
.markdown-render pre code {}/* 代码块内容 */
```

#### 4. 公式渲染专属元素

```css
.markdown-render .katex {}       /* 正常公式样式 */
.markdown-render .katex-error {} /* 公式解析失败样式 */
```

### 调用示例

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

## 三、指令 3：GetHTML - 获取渲染后的内容

### 功能

向渲染器发送指令后，获取 markdown 渲染完成后的容器内容，通过指定事件类型向父页面返回结果

### 指令参数格式

```javascript
{
    type: "GetHTML",
    listenEventType: "自定义事件类型字符串"
}
```

### 参数说明

- `type`：固定值 `GetHTML`，用于触发获取内容指令
- `listenEventType`：字符串类型，必填，父页面监听的事件类型标识，渲染器会以该类型返回结果；**注意**：当前代码存在笔误（需将 `msg.listenEvent.trim()` 修正为 `msg.listenEventType.trim()`，否则参数校验不生效）

### 调用示例（父页面JS）

```javascript
const iframe = document.getElementById('mdRenderIframe');

// 1. 父页面先监听指定事件（与listenEventType一致）
window.addEventListener('message', function (e) {
    // 匹配渲染器返回的事件类型
    if (e.data.type === 'renderContentReply') {
        console.log('获取到渲染后的内容：', e.data.html);
        // 可在此处理获取到的内容（如存储、展示等）
    }
});

// 2. 发送GetHTML指令
iframe.contentWindow.postMessage({
    type: "GetHTML",
    listenEventType: "renderContentReply" // 与监听的事件类型保持一致
}, '*');
```

### 回复格式说明

渲染器收到指令后，会通过 `window.parent.postMessage` 向父页面返回以下格式数据：

```javascript
{
    type: "自定义事件类型（即listenEventType的值）",
    html: "markdown渲染容器内的文本内容"
}
```

注：返回的 `html` 字段实际为渲染容器（`#markdownRender`）的 `textContent` 属性值，即纯文本内容，不包含HTML标签。

## 五、常规调用方式：先注入样式再渲染内容

```javascript
const iframe = document.getElementById('mdRenderIframe');
iframe.onload = function() {
    // 注入样式
    iframe.contentWindow.postMessage({
        type: "injectStyle",
        css: ".markdown-render { color: #333; font-size: 16px; }"
    }, '*');
    // 渲染内容
    iframe.contentWindow.postMessage({
        type: "SetRenderText",
        text: "# 测试标题 \n 测试内容 $E=mc^2$"
    }, '*');
};
```

## 六、控制台直接调试指令

1. 渲染 markdown 指令

```javascript
postMessage({type:'SetRenderText',text:'# 测试\n行内公式：$E=mc^2$\n```js\nconsole.log(1)\n```'}, '*');
```

1. 注入样式指令

```javascript
postMessage({type:'injectStyle',css:'.markdown-render{color:#666;padding:20px}'}, '*');
```

1. 恢复初始状态

```javascript
document.getElementById('markdownRender').innerHTML='<p>等待渲染...</p>';
```

## 七、注意事项

1. 指令 `type` 值大小写严格匹配
2. 样式未生效可添加 `!important` 强制覆盖
3. 由于JS自带转义规则，所以如果硬编码，内容中反斜杠需写双反斜杠 `\\` 转义
4. 由于JS中 \` 符号有特殊意义，所以如果硬编码，内容中的 \` 需要写反斜杠 \\\` 转义
5. 代码块需标注语言标识才能正常高亮
6. iframe 的 src 地址不可修改
7. 渲染器资源为相对路径，基于自身域名加载
8. 请确保你的设备可以稳定访问Github Pages
9. GetHTML指令需在Markdown内容渲染完成后调用，否则可能获取到 `Loading...` 文本
10. GetHTML指令的listenEventType参数需与父页面监听的事件类型严格一致，否则无法正确接收返回结果
11. GetHTML的返回内容不会包含注入的样式，若需要在其它页面展示，请额外定义样式表
12. 请在Markdown中有链接的地方使用绝对链接
