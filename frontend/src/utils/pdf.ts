/**
 * PDF 导出工具函数
 * 使用 jsPDF + html2canvas 生成 PDF
 */

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

/**
 * 将 oklch 颜色转换为 rgb 格式
 * html2canvas 不支持 oklch 颜色，需要转换
 */
function convertOklchToRgb(oklch: string): string {
  const temp = document.createElement('div');
  temp.style.color = oklch;
  temp.style.display = 'none';
  document.body.appendChild(temp);
  const rgb = getComputedStyle(temp).color;
  document.body.removeChild(temp);
  return rgb;
}

/**
 * 检查颜色值是否为 oklch 格式
 */
function isOklchColor(color: string): boolean {
  return color.includes('oklch');
}

/**
 * 递归处理元素样式，将 oklch 颜色转换为 rgb
 * 遍历所有 CSS 属性，确保不遗漏任何 oklch 颜色
 */
function processElementStyles(element: Element): void {
  const computed = window.getComputedStyle(element);
  const htmlEl = element as HTMLElement;

  // 遍历所有 CSS 属性，转换其中的 oklch 颜色
  for (let i = 0; i < computed.length; i++) {
    const prop = computed[i];
    const value = computed.getPropertyValue(prop);
    if (value && value.includes('oklch')) {
      // 使用正则替换所有 oklch 值
      const newValue = value.replace(/oklch\([^)]+\)/g, (match) => {
        return convertOklchToRgb(match);
      });
      htmlEl.style.setProperty(prop, newValue, 'important');
    }
  }

  // 递归处理子元素
  Array.from(element.children).forEach(processElementStyles);
}

/**
 * 将 DOM 元素导出为 PDF
 *
 * @param element - 要导出的 DOM 元素
 * @param filename - PDF 文件名（不含扩展名）
 */
export async function exportToPDF(element: HTMLElement, filename: string): Promise<void> {
  try {
    console.log('开始PDF导出...', element);

    // 使用 html2canvas 将 DOM 元素转换为 canvas
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
      allowTaint: true,
      scrollX: 0,
      scrollY: -window.scrollY,
      onclone: (clonedDoc, clonedElement) => {
        // 递归处理所有元素，将 oklch 颜色转换为 rgb
        processElementStyles(clonedElement);

        // 确保 PDF 导出容器样式正确
        const pdfContainer = clonedElement.querySelector('.pdf-export-container') as HTMLElement;
        if (pdfContainer) {
          pdfContainer.style.background = 'white';
        }
      },
    });

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
