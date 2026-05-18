import os
import smtplib
import yaml
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from flask import Blueprint, jsonify, request, send_file, render_template

from web_ui.conf import logger, REPORT_DIR

list_report_bp = Blueprint('list_report', __name__)

# 加载邮件配置
def load_email_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('email', {})
    except Exception as e:
        logger.error(f"加载邮件配置失败：{str(e)}")
        return {}


def send_email_with_report(recipients, report_path, report_filename):
    email_config = load_email_config()
    
    smtp_server = email_config.get('smtp_server')
    smtp_port = email_config.get('smtp_port', 465)
    sender = email_config.get('sender')
    password = email_config.get('password')
    use_ssl = email_config.get('use_ssl', True)
    subject_prefix = email_config.get('subject_prefix', '[测试报告]')
    
    if not all([smtp_server, sender, password]):
        raise Exception('邮件配置不完整，请检查 config.yml 文件')
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = f'{subject_prefix} {report_filename}'
    
    body = f"""
    <html>
    <body>
        <h2>测试报告</h2>
        <p>您好！</p>
        <p>附件为最新的测试报告，请查看。</p>
        <p>报告名称：{report_filename}</p>
        <p>生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <br/>
        <p>此邮件为系统自动发送，请勿回复。</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    
    with open(report_path, 'rb') as f:
        pdf_attachment = MIMEApplication(f.read(), _subtype="html")
        pdf_attachment.add_header('content-disposition', 'attachment', filename=report_filename)
        msg.attach(pdf_attachment)
    
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
        
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
        logger.info(f"邮件发送成功：{report_filename} -> {', '.join(recipients)}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败：{str(e)}")
        raise


@list_report_bp.route('/api/send_email_report', methods=['POST'])
def send_email_report():
    data = request.get_json()
    filename = data.get('filename')
    recipients = data.get('recipients')
    
    if not filename:
        return jsonify({'success': False, 'message': '报告文件名不能为空'}), 400
    
    if not recipients:
        return jsonify({'success': False, 'message': '收件人列表不能为空'}), 400
    
    report_path = os.path.join(REPORT_DIR, filename)
    
    if not os.path.exists(report_path):
        logger.error(f"报告文件不存在：{report_path}")
        return jsonify({'success': False, 'message': '报告文件不存在'}), 404
    
    try:
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(',') if r.strip()]
        
        send_email_with_report(recipients, report_path, filename)
        
        return jsonify({
            'success': True,
            'message': f'邮件发送成功，已发送给 {len(recipients)} 个收件人'
        })
    except Exception as e:
        logger.error(f"发送邮件失败：{str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'邮件发送失败：{str(e)}'}), 500

@list_report_bp.route('/api/reports')
def list_reports():
    logger.info(f"获取报告列表，目录：{REPORT_DIR}")

    if not os.path.exists(REPORT_DIR):
        logger.error(f"报告目录不存在：{REPORT_DIR}")
        return jsonify({'success': False, 'message': f'报告目录不存在：{REPORT_DIR}'})

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    reports = []
    try:
        for file in os.listdir(REPORT_DIR):
            if file.endswith('.html') and ('report' in file.lower() or 'Report' in file):
                file_path = os.path.join(REPORT_DIR, file)
                reports.append({
                    'filename': file,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'created_time': datetime.fromtimestamp(
                        os.path.getctime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })

        reports.sort(key=lambda x: x['created_time'], reverse=True)

        total = len(reports)
        total_pages = (total + per_page - 1) // per_page

        start = (page - 1) * per_page
        end = start + per_page
        paginated_reports = reports[start:end]

        logger.info(f"找到 {total} 个测试报告，第 {page}/{total_pages} 页")
        return jsonify({
            'success': True,
            'data': paginated_reports,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        })
    except Exception as e:
        logger.error(f"获取报告列表失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})


@list_report_bp.route('/view_report')
def view_report():
    report_path = request.args.get('path', '')
    filename = request.args.get('file', '')

    if not report_path and filename:
        report_path = os.path.join(REPORT_DIR, filename)

    logger.info(f"查看报告：{report_path}")

    if not report_path or not os.path.exists(report_path):
        logger.error(f"报告文件不存在：{report_path}")
        return jsonify({'success': False, 'message': '报告文件不存在'}), 404

    return send_file(report_path, mimetype='text/html')


@list_report_bp.route('/reports')
def reports_page():
    """报告列表页面"""
    logger.info("访问报告列表页面")
    return render_template('reports.html')