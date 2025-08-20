from weasyprint import HTML, CSS
import tempfile
import os

def test_simple_pdf():
    try:
        # 简单的HTML内容
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Test</title>
        </head>
        <body>
            <h1>Test PDF Export</h1>
            <p>This is a test document.</p>
        </body>
        </html>
        """
        
        # 简单的CSS样式
        css_content = """
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1 {
            color: blue;
        }
        """
        
        print("Creating HTML object...")
        html_doc = HTML(string=html_content)
        print("HTML object created successfully")
        
        print("Creating CSS object...")
        css_doc = CSS(string=css_content)
        print("CSS object created successfully")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        print(f"Writing PDF to: {temp_path}")
        html_doc.write_pdf(temp_path, stylesheets=[css_doc])
        print("PDF created successfully!")
        
        # 检查文件大小
        if os.path.exists(temp_path):
            size = os.path.getsize(temp_path)
            print(f"PDF file size: {size} bytes")
            os.unlink(temp_path)  # 删除临时文件
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_pdf()