import os
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file, render_template
from web_ui.conf import logger, REPORT_DIR

list_screenshots_bp = Blueprint('screenshots', __name__)


@list_screenshots_bp.route('/api/screenshots')
def list_screenshots():
    """获取截图列表"""
    screenshot_dir = os.path.join(REPORT_DIR, 'screenshots')
    logger.info(f"获取截图列表，目录：{screenshot_dir}")

    if not os.path.exists(screenshot_dir):
        logger.warning(f"截图目录不存在：{screenshot_dir}")
        return jsonify({'success': False, 'message': f'截图目录不存在：{screenshot_dir}'})

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    screenshots = []
    try:
        for file in os.listdir(screenshot_dir):
            if file.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(screenshot_dir, file)
                screenshots.append({
                    'filename': file,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'created_time': datetime.fromtimestamp(
                        os.path.getctime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })

        screenshots.sort(key=lambda x: x['created_time'], reverse=True)

        total = len(screenshots)
        total_pages = (total + per_page - 1) // per_page

        start = (page - 1) * per_page
        end = start + per_page
        paginated_screenshots = screenshots[start:end]

        logger.info(f"找到 {total} 个截图，第 {page}/{total_pages} 页")
        return jsonify({
            'success': True,
            'data': paginated_screenshots,
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
        logger.error(f"获取截图列表失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})


@list_screenshots_bp.route('/view_screenshot')
def view_screenshot():
    """查看单个截图"""
    filename = request.args.get('file', '')

    if not filename:
        logger.error("查看截图失败：未提供文件名")
        return jsonify({'success': False, 'message': '未提供文件名'}), 400

    screenshot_path = os.path.join(REPORT_DIR, 'screenshots', filename)
    logger.info(f"查看截图：{screenshot_path}")

    if not os.path.exists(screenshot_path):
        logger.error(f"截图文件不存在：{screenshot_path}")
        return jsonify({'success': False, 'message': '截图文件不存在'}), 404

    return send_file(screenshot_path, mimetype='image/png')


@list_screenshots_bp.route('/screenshots')
def screenshots_page():
    """截图列表页面"""
    logger.info("访问截图列表页面")
    return render_template('screenshots.html')
