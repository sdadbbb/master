import os
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file, render_template

from web_ui.conf import logger, REPORT_DIR

list_report_bp = Blueprint('list_report', __name__)


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