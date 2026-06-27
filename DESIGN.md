---
name: 户外策划
description: 从两步路 URL 到可靠户外策划的单任务工作台
colors:
  primary: "#245C3A"
  primary-hover: "#19452B"
  canvas: "#F5F7F5"
  surface: "#FFFFFF"
  text: "#17201B"
  text-muted: "#667069"
  border: "#DCE3DE"
  success: "#16794A"
  warning: "#A45A08"
  danger: "#B42318"
typography:
  display:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2rem, 5vw, 3.5rem)"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.035em"
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "12px 18px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "12px 14px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "24px"
---

# Design System: 户外策划

## Overview

**Creative North Star: "行前地图桌"**

界面应像一张整理清楚的行前地图桌：重要输入、当前状态和下一步一眼可见。信息密度适中，层级靠排版、留白和细边框建立，不靠装饰制造“户外感”。

系统明确拒绝玻璃拟态、彩色渐变、巨大圆角、装饰性山脉 SVG、无意义动效和泛 AI SaaS 营销页。

**Key Characteristics:**

- 单列主任务，桌面端辅以窄侧栏说明。
- 真实状态优先于宣传文案。
- 移动端可单手完成粘贴、查看授权进度和定位；扫码与验证码在本机授权窗口完成。

## Colors

森林绿只承担主操作和关键进度，其他区域保持中性。

**The One Trail Rule.** 同一屏只允许一个高强调主操作，主色不用于大面积背景。

## Typography

全产品使用单一的人文无衬线字体栈，标题靠字重、尺寸和紧凑字距形成层级。

**The Plain Language Rule.** 标签使用用户语言，例如“两步路线路 URL”，不把接口名和内部状态暴露为主文案。

## Elevation

默认无阴影，以白色表面、浅灰画布和 1px 边框分层。仅浮层和需要脱离页面的提示使用低对比环境阴影。

**The Flat-by-Default Rule.** 静止表面保持平坦；如果一个普通卡片靠阴影才看得见，说明层级设计失败。

## Components

### Buttons

- 主按钮使用森林绿、白字和 12px 圆角。
- `hover` 仅加深颜色，`focus-visible` 使用清晰的绿色焦点环。
- 次按钮使用白色表面和 1px 中性边框。

### Cards / Containers

- 普通容器使用 16px 圆角、白色表面和 1px 边框。
- 同一逻辑步骤只使用一个容器，禁止卡片套卡片。

### Inputs / Fields

- 输入框高度至少 44px，标签始终可见。
- 错误同时使用文字和颜色表达；定位失败后保留手动输入。

### Navigation

- 只保留“开始策划”和“API 配置”两个入口。
- 当前页通过文字权重和主色标识，不使用彩色胶囊导航。

## Do's and Don'ts

### Do:

- **Do** 让 URL 输入和“打开授权窗口”成为首屏最高优先级。
- **Do** 清楚区分“等待登录、人工验证、正在下载、轨迹就绪”。
- **Do** 为定位权限拒绝、浏览器不支持和反向地理编码失败提供手动填写退路。

### Don't:

- **Don't** 使用玻璃拟态、彩色渐变、巨大圆角、装饰性山脉 SVG 和无意义动效。
- **Don't** 用多个卡片重复解释同一件事。
- **Don't** 把 API 配置、技术名词或次要工具放在主流程之前。
- **Don't** 用“已授权”“已下载”等文案掩盖尚未验证的外部状态。
