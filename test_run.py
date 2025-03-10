import os
import pytest
import tempfile

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QDialogButtonBox, QListWidgetItem

import run  # run.py 파일이 동일한 디렉토리에 있어야 함


def test_list_item_widget(qtbot):
    """ListItemWidget이 filename을 올바르게 표시하고, show_check() 호출 시 아이콘이 설정되는지 테스트."""
    widget = run.ListItemWidget("test_file.txt")
    qtbot.addWidget(widget)
    assert widget.label.text() == "test_file.txt"
    # 호출 후 check_label의 pixmap이 설정되어 있는지 확인
    widget.show_check()
    assert widget.check_label.pixmap() is not None


def test_custom_list_widget_delete(qtbot):
    """CustomListWidget에서 Delete 키 입력 시 선택된 아이템이 삭제되는지 테스트."""
    widget = run.CustomListWidget()
    qtbot.addWidget(widget)
    # 두 개의 아이템 추가
    item1 = QListWidgetItem("Item 1")
    item1.setData(Qt.UserRole, "dummy1")
    widget.addItem(item1)
    item2 = QListWidgetItem("Item 2")
    item2.setData(Qt.UserRole, "dummy2")
    widget.addItem(item2)
    initial_count = widget.count()
    # 첫 번째 아이템 선택
    widget.setCurrentRow(0)
    # Delete 키 이벤트 시뮬레이션
    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
    widget.keyPressEvent(event)
    # 아이템 개수가 1개로 줄었는지 확인
    assert widget.count() == initial_count - 1


def test_save_settings_dialog_toggle_csv(qtbot):
    """SaveSettingsDialog의 CSV 체크박스 토글에 따른 csv_edit 활성화/비활성화를 테스트."""
    dialog = run.SaveSettingsDialog()
    qtbot.addWidget(dialog)
    # CSV 체크박스가 선택된 상태라면 csv_edit는 활성화되어 있어야 함
    dialog.csv_checkbox.setChecked(True)
    dialog.toggle_csv_edit(True)
    assert dialog.csv_edit.isEnabled() is True
    # CSV 체크박스가 해제되면 csv_edit가 비활성화되어야 함
    dialog.toggle_csv_edit(False)
    assert dialog.csv_edit.isEnabled() is False
    # get_values() 메서드의 반환값 확인 (튜플 5개 요소)
    values = dialog.get_values()
    assert isinstance(values, tuple)
    assert len(values) == 5


def test_help_dialog(qtbot):
    """HelpDialog가 올바르게 표시되고, OK 버튼 클릭 시 종료되는지 테스트."""
    dialog = run.HelpDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    buttons = dialog.findChild(QDialogButtonBox)
    # OK 버튼 클릭 (대화상자 수락)
    ok_button = buttons.button(QDialogButtonBox.Ok)
    qtbot.mouseClick(ok_button, Qt.LeftButton)
    qtbot.waitUntil(lambda: not dialog.isVisible())


def test_about_dialog(qtbot):
    """AboutDialog가 올바르게 표시되고, OK 버튼 클릭 시 종료되는지 테스트."""
    dialog = run.AboutDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    buttons = dialog.findChild(QDialogButtonBox)
    ok_button = buttons.button(QDialogButtonBox.Ok)
    qtbot.mouseClick(ok_button, Qt.LeftButton)
    qtbot.waitUntil(lambda: not dialog.isVisible())


def test_main_window_open_file(qtbot, monkeypatch):
    """MainWindow의 open_file 메서드가 파일 선택 후 리스트에 아이템을 추가하는지 테스트."""
    # QFileDialog.getOpenFileNames를 monkeypatch로 대체
    fake_file = "/path/to/fake_image.jpg"
    monkeypatch.setattr(run.QFileDialog, "getOpenFileNames", lambda *args, **kwargs: ([fake_file], ""))
    
    window = run.MainWindow()
    qtbot.addWidget(window)
    window.open_file()
    # 리스트 위젯에 하나의 아이템이 추가되어야 함
    assert window.list_widget.count() == 1
    item = window.list_widget.item(0)
    assert item.data(Qt.UserRole) == fake_file


def test_main_window_open_folder(qtbot, monkeypatch, tmp_path):
    """MainWindow의 open_folder 메서드가 폴더 내 이미지 파일들을 리스트에 추가하는지 테스트."""
    # 임시 폴더에 더미 이미지 파일 생성
    test_folder = tmp_path / "images"
    test_folder.mkdir()
    fake_image1 = test_folder / "image1.jpg"
    fake_image1.write_bytes(b"dummy data")
    fake_image2 = test_folder / "image2.png"
    fake_image2.write_bytes(b"dummy data")
    # getExistingDirectory를 monkeypatch로 대체하여 임시 폴더 반환
    monkeypatch.setattr(run.QFileDialog, "getExistingDirectory", lambda *args, **kwargs: str(test_folder))
    
    window = run.MainWindow()
    qtbot.addWidget(window)
    window.open_folder()
    # 두 개의 이미지 파일이 리스트에 추가되어야 함
    assert window.list_widget.count() == 2


def test_main_window_run_model_no_file(qtbot, monkeypatch):
    """MainWindow의 run_model 메서드가 파일이 없을 때 경고 메시지를 띄우는지 테스트."""
    window = run.MainWindow()
    qtbot.addWidget(window)
    # 리스트 위젯을 비워둠 (파일 없음)
    window.list_widget.clear()
    
    warning_called = False

    def fake_warning(*args, **kwargs):
        nonlocal warning_called
        warning_called = True

    monkeypatch.setattr(run.QMessageBox, "warning", fake_warning)
    window.run_model()
    assert warning_called