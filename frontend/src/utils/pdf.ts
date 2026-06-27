/**
 * 报告导出工具（防卡死版）
 * ----------------------
 * - PDF：走浏览器原生 `window.print()`。纯原生打印管线，不克隆 DOM、不画大 Canvas、
 *   不阻塞主线程，自动分页。用户在打印对话框里选「另存为 PDF」即可。
 *   彻底告别 html2canvas + jsPDF 在长页面（地图/图表/大表格）上卡死/崩溃的问题。
 * - 长图：用 modern-screenshot（比 html2canvas 快数十倍、内存占用更低），导出时由
 *   调用方禁用按钮并显示 loading。
 */

const PRINT_STYLE_ID = 'report-print-style';
// 只显示报告主内容区，隐藏导航/按钮等；其余交给浏览器原生分页。
const PRINT_CSS = `
@media print {
  body * { visibility: hidden !important; }
  .pdf-export-container, .pdf-export-container * { visibility: visible !important; }
  .pdf-export-container {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  .no-print { display: none !important; }
}
`;

function sanitizeFilename(filename: string): string {
  const cleaned = filename.replace(/[\\/:*?"<>|]/g, '_').trim();
  return cleaned || '户外策划书';
}

function ensurePrintStyle(): void {
  if (document.getElementById(PRINT_STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = PRINT_STYLE_ID;
  style.textContent = PRINT_CSS;
  document.head.appendChild(style);
}

/**
 * 导出 PDF：触发浏览器原生打印。在弹出的打印对话框中选择「另存为 PDF」。
 * 不传元素——打印范围由 PRINT_CSS 里的 .pdf-export-container 决定。
 */
export async function exportToPDF(): Promise<void> {
  ensurePrintStyle();
  // 等一帧让 <style> 生效后再触发打印
  await new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 0)));
  window.print();
}

/**
 * 导出长图 PNG：modern-screenshot 渲染整段内容。速度远快于 html2canvas。
 * 注意：超长页面仍受浏览器 Canvas 尺寸/内存上限约束；地图瓦片跨域可能不显示。
 */
export async function exportToLongImage(element: HTMLElement, filename: string): Promise<void> {
  const { domToPng } = await import('modern-screenshot');
  const dataUrl = await domToPng(element, {
    scale: Math.min(window.devicePixelRatio || 2, 2),
    backgroundColor: '#ffffff',
    fetch: { requestInit: { mode: 'cors' } },
  });

  const link = document.createElement('a');
  link.href = dataUrl;
  link.download = `${sanitizeFilename(filename)}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
