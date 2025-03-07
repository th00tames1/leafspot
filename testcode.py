import sys
import os
import unittest
from unittest.mock import patch, MagicMock

import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QDialog, QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt

# main_app.py 파일(또는 해당 모듈명)에서 필요한 클래스들을 import 합니다.
# 예: from main_app import MainWindow, SaveSettingsDialog, ListItemWidget
# 여기서는 편의를 위해 동일 파일 내에 정의된 것으로 가정합니다.
from run import MainWindow, SaveSettingsDialog, ListItemWidget

# 더미 결과 및 모델 객체 (실제 YOLO 대신 사용)
class DummyResult:
    def __init__(self):
        self.boxes = None
        self.masks = None
    def plot(self, boxes=False, labels=False, conf=False):
        # 단순 흰색 이미지 반환 (600x600, 3채널)
        return 255 * np.ones((600, 600, 3), dtype=np.uint8)

class DummyModel:
    def __call__(self, image_path, conf, imgsz):
        # 항상 DummyResult 하나를 담은 리스트 반환
        return [DummyResult()]

class TestSaveSettingsDialog(unittest.TestCase):
    def setUp(self):
        # 테스트를 위해 대화상자 인스턴스를 생성합니다.
        self.dialog = SaveSettingsDialog()

    def test_toggle_csv_edit(self):
        # 초기에는 csv_edit가 활성 상태여야 합니다.
        self.assertTrue(self.dialog.csv_edit.isEnabled())
        # 체크박스를 해제하면 csv_edit가 비활성화 되어야 합니다.
        self.dialog.csv_checkbox.setChecked(False)
        self.assertFalse(self.dialog.csv_edit.isEnabled())
        # 다시 체크하면 csv_edit가 활성화되어야 합니다.
        self.dialog.csv_checkbox.setChecked(True)
        self.assertTrue(self.dialog.csv_edit.isEnabled())

class TestListItemWidget(unittest.TestCase):
    def test_show_check(self):
        widget = ListItemWidget("testfile.jpg")
        # 초기에는 체크 아이콘이 설정되어 있지 않아야 함
        self.assertIsNone(widget.check_label.pixmap())
        widget.show_check()
        # show_check 호출 후 pixmap이 설정되어 있어야 함
        self.assertIsNotNone(widget.check_label.pixmap())

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        # QApplication이 이미 존재하지 않으면 생성합니다.
        if QApplication.instance() is None:
            self.app = QApplication(sys.argv)
        self.window = MainWindow()
        # 실제 모델 대신 DummyModel을 할당하여 예측 시간이 걸리지 않도록 합니다.
        self.window.pred_model = DummyModel()
        # 테스트용으로 list_widget을 초기화합니다.
        self.window.list_widget.clear()

    def test_run_model_no_files(self):
        # 리스트가 비어 있는 상태에서 run_model() 호출 시 경고 메시지가 뜨는지 확인합니다.
        with patch.object(QMessageBox, 'warning') as mock_warning:
            self.window.run_model()
            mock_warning.assert_called_once_with(
                self.window, "Warning", "Please load a file or folder before running the model."
            )

    def test_run_model_with_file(self):
        # 리스트에 더미 파일을 추가합니다.
        dummy_file = os.path.join(os.getcwd(), "dummy.jpg")
        item = QListWidgetItem()
        widget = ListItemWidget("dummy.jpg")
        item.setData(Qt.UserRole, dummy_file)
        self.window.list_widget.addItem(item)
        self.window.list_widget.setItemWidget(item, widget)

        # SaveSettingsDialog를 더미 대화상자로 대체하여 자동으로 테스트 값을 반환하게 합니다.
        class DummyDialog:
            def exec_(self):
                return QDialog.Accepted
            def get_values(self):
                # 테스트를 위해 현재 디렉토리와 간단한 prefix, suffix, CSV 옵션 값을 반환
                return (os.getcwd(), "prefix", "suffix", True, "detection.csv")
        
        with patch('main_app.SaveSettingsDialog', return_value=DummyDialog()):
            # QMessageBox.information 호출을 무시하여 모달 대화상자가 뜨지 않도록 함
            with patch.object(QMessageBox, 'information'):
                self.window.run_model()
                # run_model() 실행 후 해당 리스트 아이템의 체크 아이콘이 설정되었는지 확인합니다.
                widget_after = self.window.list_widget.itemWidget(item)
                self.assertIsNotNone(widget_after.check_label.pixmap())

if __name__ == '__main__':
    unittest.main()
