import os
import pytest
import tempfile

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QDialogButtonBox, QListWidgetItem

import run  # The run.py file must be in the same directory


def test_list_item_widget(qtbot):
    """Test that ListItemWidget displays the filename correctly and that calling show_check() sets the icon."""
    widget = run.ListItemWidget("test_file.txt")
    qtbot.addWidget(widget)
    assert widget.label.text() == "test_file.txt"
    # Verify that after calling show_check(), the pixmap in check_label is set
    widget.show_check()
    assert widget.check_label.pixmap() is not None


def test_custom_list_widget_delete(qtbot):
    """Test that pressing the Delete key in CustomListWidget deletes the selected item."""
    widget = run.CustomListWidget()
    qtbot.addWidget(widget)
    # Add two items
    item1 = QListWidgetItem("Item 1")
    item1.setData(Qt.UserRole, "dummy1")
    widget.addItem(item1)
    item2 = QListWidgetItem("Item 2")
    item2.setData(Qt.UserRole, "dummy2")
    widget.addItem(item2)
    initial_count = widget.count()
    # Select the first item
    widget.setCurrentRow(0)
    # Simulate a Delete key event
    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
    widget.keyPressEvent(event)
    # Verify that the number of items has decreased by one
    assert widget.count() == initial_count - 1


def test_save_settings_dialog_toggle_csv(qtbot):
    """Test the enabling/disabling of csv_edit in SaveSettingsDialog when toggling the CSV checkbox."""
    dialog = run.SaveSettingsDialog()
    qtbot.addWidget(dialog)
    # When the CSV checkbox is checked, csv_edit should be enabled
    dialog.csv_checkbox.setChecked(True)
    dialog.toggle_csv_edit(True)
    assert dialog.csv_edit.isEnabled() is True
    # When the CSV checkbox is unchecked, csv_edit should be disabled
    dialog.toggle_csv_edit(False)
    assert dialog.csv_edit.isEnabled() is False
    # Verify that the get_values() method returns a tuple with 5 elements
    values = dialog.get_values()
    assert isinstance(values, tuple)
    assert len(values) == 5


def test_help_dialog(qtbot):
    """Test that HelpDialog is displayed correctly and that clicking the OK button closes the dialog."""
    dialog = run.HelpDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    buttons = dialog.findChild(QDialogButtonBox)
    # Click the OK button (accept the dialog)
    ok_button = buttons.button(QDialogButtonBox.Ok)
    qtbot.mouseClick(ok_button, Qt.LeftButton)
    qtbot.waitUntil(lambda: not dialog.isVisible())


def test_about_dialog(qtbot):
    """Test that AboutDialog is displayed correctly and that clicking the OK button closes the dialog."""
    dialog = run.AboutDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    buttons = dialog.findChild(QDialogButtonBox)
    ok_button = buttons.button(QDialogButtonBox.Ok)
    qtbot.mouseClick(ok_button, Qt.LeftButton)
    qtbot.waitUntil(lambda: not dialog.isVisible())


def test_main_window_open_file(qtbot, monkeypatch):
    """Test that MainWindow's open_file method adds an item to the list after a file is selected."""
    # Replace QFileDialog.getOpenFileNames with a monkeypatch
    fake_file = "/path/to/fake_image.jpg"
    monkeypatch.setattr(run.QFileDialog, "getOpenFileNames", lambda *args, **kwargs: ([fake_file], ""))
    
    window = run.MainWindow()
    qtbot.addWidget(window)
    window.open_file()
    # One item should be added to the list widget
    assert window.list_widget.count() == 1
    item = window.list_widget.item(0)
    assert item.data(Qt.UserRole) == fake_file


def test_main_window_open_folder(qtbot, monkeypatch, tmp_path):
    """Test that MainWindow's open_folder method adds image files from a folder to the list."""
    # Create dummy image files in a temporary folder
    test_folder = tmp_path / "images"
    test_folder.mkdir()
    fake_image1 = test_folder / "image1.jpg"
    fake_image1.write_bytes(b"dummy data")
    fake_image2 = test_folder / "image2.png"
    fake_image2.write_bytes(b"dummy data")
    # Replace getExistingDirectory with a monkeypatch that returns the temporary folder
    monkeypatch.setattr(run.QFileDialog, "getExistingDirectory", lambda *args, **kwargs: str(test_folder))
    
    window = run.MainWindow()
    qtbot.addWidget(window)
    window.open_folder()
    # Two image files should be added to the list widget
    assert window.list_widget.count() == 2


def test_main_window_run_model_no_file(qtbot, monkeypatch):
    """Test that MainWindow's run_model method displays a warning message when no files are present."""
    window = run.MainWindow()
    qtbot.addWidget(window)
    # Clear the list widget (no files)
    window.list_widget.clear()
    
    warning_called = False

    def fake_warning(*args, **kwargs):
        nonlocal warning_called
        warning_called = True

    monkeypatch.setattr(run.QMessageBox, "warning", fake_warning)
    window.run_model()
    assert warning_called
