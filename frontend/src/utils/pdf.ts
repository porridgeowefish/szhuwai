/**
 * PDF 导出工具函数
 * 使用 jsPDF + html2canvas 生成 PDF
 */

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

/**
 * 将 DOM 元素导出为 PDF
 *
 * @param element - 要导出的 DOM 元素
 * @param filename - PDF 文件名（不含扩展名）
 */
export async function exportToPDF(element: HTMLElement, filename: string): Promise<void> {
  try {
    console.log('开始PDF导出...', element);

    // 创建一个临时容器来清理样式
    const tempContainer = document.createElement('div');
    tempContainer.style.position = 'absolute';
    tempContainer.style.left = '-9999px';
    tempContainer.style.top = '0';
    document.body.appendChild(tempContainer);

    // 克隆元素
    const clonedElement = element.cloneNode(true) as HTMLElement;
    tempContainer.appendChild(clonedElement);

    // 移除所有包含 oklch 的 style 标签
    const removeOklchStyles = () => {
      const styleSheets = document.styleSheets;
      try {
        for (let i = 0; i < styleSheets.length; i++) {
          const sheet = styleSheets[i];
          try {
            const cssRules = sheet.cssRules || sheet.rules;
            if (cssRules) {
              for (let j = cssRules.length - 1; j >= 0; j--) {
                const rule = cssRules[j];
                if (rule.cssText && rule.cssText.includes('oklch')) {
                  sheet.deleteRule(j);
                }
              }
            }
          } catch (e) {
            // 跨域样式表无法访问
          }
        }
      } catch (e) {
        console.warn('清理样式失败', e);
      }
    };

    // 使用 html2canvas 将 DOM 元素转换为 canvas
    const canvas = await html2canvas(clonedElement, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
      allowTaint: true,
      onclone: (clonedDoc) => {
        // 删除所有 link 和 style 标签，重新添加纯色样式
        const styles = clonedDoc.createElement('style');
        styles.textContent = `
          /* 覆盖所有可能使用 oklch 的颜色 */
          * {
            all: revert !important;
            color: rgb(0, 0, 0) !important;
            background-color: rgb(255, 255, 255) !important;
          }
          .text-red-50, .text-red-100, .text-red-200, .text-red-300, .text-red-400,
          .text-red-500, .text-red-600, .text-red-700, .text-red-800, .text-red-900 { color: rgb(220, 38, 38) !important; }
          .text-blue-50, .text-blue-100, .text-blue-200, .text-blue-300, .text-blue-400,
          .text-blue-500, .text-blue-600, .text-blue-700, .text-blue-800, .text-blue-900 { color: rgb(37, 99, 235) !important; }
          .text-emerald-50, .text-emerald-100, .text-emerald-200, .text-emerald-300, .text-emerald-400,
          .text-emerald-500, .text-emerald-600, .text-emerald-700, .text-emerald-800, .text-emerald-900 { color: rgb(16, 185, 129) !important; }
          .text-amber-50, .text-amber-100, .text-amber-200, .text-amber-300, .text-amber-400,
          .text-amber-500, .text-amber-600, .text-amber-700, .text-amber-800, .text-amber-900 { color: rgb(245, 158, 11) !important; }
          .text-zinc-50, .text-zinc-100, .text-zinc-200, .text-zinc-300, .text-zinc-400,
          .text-zinc-500, .text-zinc-600, .text-zinc-700, .text-zinc-800, .text-zinc-900 { color: rgb(63, 63, 70) !important; }
          .text-indigo-50, .text-indigo-100, .text-indigo-200, .text-indigo-300, .text-indigo-400,
          .text-indigo-500, .text-indigo-600, .text-indigo-700, .text-indigo-800, .text-indigo-900 { color: rgb(99, 102, 241) !important; }
          .bg-red-50, .bg-red-100, .bg-red-200, .bg-red-300, .bg-red-400,
          .bg-red-500, .bg-red-600, .bg-red-700, .bg-red-800, .bg-red-900 { background-color: rgb(254, 242, 242) !important; }
          .bg-blue-50, .bg-blue-100, .bg-blue-200, .bg-blue-300, .bg-blue-400,
          .bg-blue-500, .bg-blue-600, .bg-blue-700, .bg-blue-800, .bg-blue-900 { background-color: rgb(239, 246, 255) !important; }
          .bg-emerald-50, .bg-emerald-100, .bg-emerald-200, .bg-emerald-300, .bg-emerald-400,
          .bg-emerald-500, .bg-emerald-600, .bg-emerald-700, .bg-emerald-800, .bg-emerald-900 { background-color: rgb(236, 253, 245) !important; }
          .bg-amber-50, .bg-amber-100, .bg-amber-200, .bg-amber-300, .bg-amber-400,
          .bg-amber-500, .bg-amber-600, .bg-amber-700, .bg-amber-800, .bg-amber-900 { background-color: rgb(254, 243, 199) !important; }
          .bg-zinc-50, .bg-zinc-100, .bg-zinc-200, .bg-zinc-300, .bg-zinc-400,
          .bg-zinc-500, .bg-zinc-600, .bg-zinc-700, .bg-zinc-800, .bg-zinc-900 { background-color: rgb(250, 250, 250) !important; }
          .bg-indigo-50, .bg-indigo-100, .bg-indigo-200, .bg-indigo-300, .bg-indigo-400,
          .bg-indigo-500, .bg-indigo-600, .bg-indigo-700, .bg-indigo-800, .bg-indigo-900 { background-color: rgb(238, 242, 255) !important; }
          .bg-white { background-color: rgb(255, 255, 255) !important; }
          .text-white { color: rgb(255, 255, 255) !important; }
          .text-black { color: rgb(0, 0, 0) !important; }
        `;
        clonedDoc.head.appendChild(styles);
      },
    });

    // 清理临时容器
    document.body.removeChild(tempContainer);

    console.log('Canvas生成完成', canvas.width, canvas.height);

    // 获取 canvas 尺寸
    const imgWidth = canvas.width;
    const imgHeight = canvas.height;

    // 创建 PDF (A4 尺寸)
    const pdf = new jsPDF({
      orientation: imgWidth > imgHeight ? 'landscape' : 'portrait',
      unit: 'px',
      format: 'a4',
    });

    // A4 纸张尺寸 (像素)
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();

    console.log('PDF尺寸', pdfWidth, pdfHeight);

    // 计算缩放比例以适应页面
    const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
    const scaledWidth = imgWidth * ratio;
    const scaledHeight = imgHeight * ratio;

    console.log('缩放比例', ratio, scaledWidth, scaledHeight);

    // 居中放置
    const x = (pdfWidth - scaledWidth) / 2;
    const y = (pdfHeight - scaledHeight) / 2;

    // 将 canvas 转换为图片并添加到 PDF
    const imgData = canvas.toDataURL('image/png');
    pdf.addImage(imgData, 'PNG', x, y, scaledWidth, scaledHeight);

    // 下载 PDF
    pdf.save(`${filename}.pdf`);
    console.log('PDF导出成功');
  } catch (error) {
    console.error('PDF 导出失败:', error);
    alert(`PDF导出失败: ${error instanceof Error ? error.message : '未知错误'}`);
    throw error;
  }
}