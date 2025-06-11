import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO


# 用于添加文本的函数
def add_text_to_pdf(input_pdf_path, text):
    # 创建一个临时的 PDF 文件用于绘制文字
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    width, height = letter

    # 设置中文字体（可以选择更大的字体）
    c.setFont("Helvetica-Bold", 18)  # 增大字体到 18

    # 在右上角添加文字
    c.drawString(width - 150, height - 30, text)  # 文字位置
    c.save()

    # 将文本 PDF 添加到输入 PDF 上
    packet.seek(0)
    text_pdf = PdfReader(packet)
    input_pdf = PdfReader(input_pdf_path)

    output_pdf = PdfWriter()

    # 合并每页
    for i in range(len(input_pdf.pages)):
        page = input_pdf.pages[i]
        page.merge_page(text_pdf.pages[0])  # 合并文字
        output_pdf.add_page(page)

    return output_pdf


# 合并PDF文件并添加文件名
def merge_pdfs_with_text(pdf_paths, output_path):
    pdf_writer = PdfWriter()

    for pdf_path in pdf_paths:
        filename = os.path.splitext(os.path.basename(pdf_path))[0]  # 去掉文件后缀
        # 生成文本
        text = f"{filename} Month OKR"

        # 添加文本到 PDF
        output_pdf = add_text_to_pdf(pdf_path, text)

        # 将处理后的页面添加到总的 PDF 中
        for page in output_pdf.pages:
            pdf_writer.add_page(page)

    # 输出合并后的 PDF 文件
    with open(output_path, "wb") as output_file:
        pdf_writer.write(output_file)


# 获取okrs文件夹中的所有pdf文件
pdf_folder = "okrs"
pdf_files = sorted(
    [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.endswith(".pdf")],
    key=lambda x: int(os.path.splitext(os.path.basename(x))[0])  # 按文件名数字排序
)
output_file = "merged_output.pdf"

# 调用合并函数
merge_pdfs_with_text(pdf_files, output_file)

print(f"合并后的PDF文件已保存为 {output_file}")
