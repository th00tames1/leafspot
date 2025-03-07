import sys
import os
import cv2
import numpy as np
import qtawesome as qta
import csv

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QFileDialog, QVBoxLayout,
    QHBoxLayout, QGridLayout, QProgressBar, QMessageBox, QDialog,
    QLineEdit, QDialogButtonBox, QAbstractItemView, QMenu, QCheckBox,
    QTabWidget, QGroupBox
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, QSettings

from ultralytics import YOLO

class ListItemWidget(QWidget):
    def __init__(self, filename, parent=None):
        """Initialize a list widget item showing a filename."""
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        self.label = QLabel(filename)
        layout.addWidget(self.label)
        layout.addStretch()
        self.check_label = QLabel()
        layout.addWidget(self.check_label)
    
    def show_check(self):
        """Display a green check icon on the widget."""
        pixmap = qta.icon('fa.check', color='green').pixmap(16, 16)
        self.check_label.setPixmap(pixmap)

class CustomListWidget(QListWidget):
    def keyPressEvent(self, event):
        """Handle key press events; delete selected items on Delete key."""
        if event.key() == Qt.Key_Delete:
            for item in self.selectedItems():
                self.takeItem(self.row(item))
        else:
            super().keyPressEvent(event)
    
    def contextMenuEvent(self, event):
        """Display context menu with delete option."""
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            for item in self.selectedItems():
                self.takeItem(self.row(item))

class SaveSettingsDialog(QDialog):
    def __init__(self, parent=None):
        """Dialog for configuring save settings (used when running the model)."""
        super().__init__(parent)
        self.setWindowTitle("Save Settings")
        self.settings = QSettings("YourCompany", "OSULeafSpotDetector")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(5)

        label_save_path = QLabel("Save Path")
        layout.addWidget(label_save_path)
        
        # Save path with default current directory and folder icon without overlap
        self.dir_edit = QLineEdit(os.getcwd())
        self.dir_edit.setPlaceholderText("Select save directory")
        action = self.dir_edit.addAction(qta.icon('fa.folder', color='orange'), QLineEdit.TrailingPosition)
        action.triggered.connect(self.browse_directory)
        self.dir_edit.setTextMargins(0, 0, 30, 0)
        layout.addWidget(self.dir_edit)

        optional_label = QLabel("Optional")
        layout.addWidget(optional_label)

        self.prefix_edit = QLineEdit(self.settings.value("save/prefix", ""))
        self.prefix_edit.setPlaceholderText("Enter filename prefix")
        layout.addWidget(self.prefix_edit)

        self.suffix_edit = QLineEdit(self.settings.value("save/suffix", ""))
        self.suffix_edit.setPlaceholderText("Enter filename suffix")
        layout.addWidget(self.suffix_edit)
        
        self.csv_checkbox = QCheckBox("Extract .csv file")
        self.csv_checkbox.setChecked(self.settings.value("save/csv_enabled", True, type=bool))
        layout.addWidget(self.csv_checkbox)
        
        self.csv_edit = QLineEdit(self.settings.value("save/csv_filename", "detection.csv"))
        layout.addWidget(self.csv_edit)
        
        self.csv_checkbox.toggled.connect(self.toggle_csv_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def toggle_csv_edit(self, checked):
        """Enable or disable CSV filename edit based on checkbox."""
        self.csv_edit.setEnabled(checked)
        
    def browse_directory(self):
        """Open a directory dialog to select a save folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if folder:
            self.dir_edit.setText(folder)
            
    def get_values(self):
        """Return the save settings values."""
        return (self.dir_edit.text(), 
                self.prefix_edit.text(), 
                self.suffix_edit.text(), 
                self.csv_checkbox.isChecked(), 
                self.csv_edit.text())

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        """Dialog for configuring all settings (View, Save, Advanced)."""
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 400)
        self.settings = QSettings("YourCompany", "OSULeafSpotDetector")
        self.tab_widget = QTabWidget()
        
        self.view_tab = QWidget()
        self.save_tab = QWidget()
        self.advanced_tab = QWidget()
        self.tab_widget.addTab(self.view_tab, "View Settings")
        self.tab_widget.addTab(self.save_tab, "Save Settings")
        self.tab_widget.addTab(self.advanced_tab, "Advanced Settings")
        
        # --- View Settings Tab ---
        view_layout = QVBoxLayout(self.view_tab)
        view_layout.setAlignment(Qt.AlignTop)
        view_layout.setSpacing(5)
        
        # Create Label Settings group
        label_group = QGroupBox("Label Settings")
        label_layout = QVBoxLayout(label_group)
        label_layout.setSpacing(5)
        self.cb_show_leaf_label = QCheckBox("Show Leaf Area Label")
        self.cb_show_spot_label = QCheckBox("Show Spot Area Label")
        self.cb_show_count = QCheckBox("Show Count")
        self.cb_show_percent = QCheckBox("Show Percentage")
        self.cb_show_leaf_label.setChecked(self.settings.value("view/show_leaf", True, type=bool))
        self.cb_show_spot_label.setChecked(self.settings.value("view/show_spot", True, type=bool))
        self.cb_show_count.setChecked(self.settings.value("view/show_count", True, type=bool))
        self.cb_show_percent.setChecked(self.settings.value("view/show_percent", True, type=bool))
        label_layout.addWidget(self.cb_show_leaf_label)
        label_layout.addWidget(self.cb_show_spot_label)
        label_layout.addWidget(self.cb_show_count)
        label_layout.addWidget(self.cb_show_percent)
        view_layout.addWidget(label_group)
        
        # Create Graph Settings group
        graph_group = QGroupBox("Graph Settings")
        graph_layout = QVBoxLayout(graph_group)
        graph_layout.setSpacing(5)
        self.cb_show_box = QCheckBox("Show Bounding Box")
        self.cb_show_label = QCheckBox("Show Label")
        self.cb_show_conf = QCheckBox("Show Confidence")
        self.cb_show_box.setChecked(self.settings.value("view/show_box", False, type=bool))
        self.cb_show_label.setChecked(self.settings.value("view/show_label", False, type=bool))
        self.cb_show_conf.setChecked(self.settings.value("view/show_conf", False, type=bool))
        graph_layout.addWidget(self.cb_show_box)
        graph_layout.addWidget(self.cb_show_label)
        graph_layout.addWidget(self.cb_show_conf)
        view_layout.addWidget(graph_group)
        
        # Connect state changes for enabling/disabling sub-items
        self.cb_show_leaf_label.stateChanged.connect(self.update_label_settings)
        self.cb_show_spot_label.stateChanged.connect(self.update_label_settings)
        self.cb_show_box.stateChanged.connect(self.update_graph_settings)
        
        # --- Save Settings Tab ---
        save_layout = QVBoxLayout(self.save_tab)
        save_layout.setAlignment(Qt.AlignTop)
        save_layout.setSpacing(5)
        self.le_save_path = QLineEdit(self.settings.value("save/save_path", os.getcwd()))
        save_layout.addWidget(QLabel("Save Path:"))
        action = self.le_save_path.addAction(qta.icon('fa.folder', color='orange'), QLineEdit.TrailingPosition)
        action.triggered.connect(self.browse_save_path)
        self.le_save_path.setTextMargins(0, 0, 30, 0)
        save_layout.addWidget(self.le_save_path)
        
        self.le_prefix = QLineEdit(self.settings.value("save/prefix", ""))
        save_layout.addWidget(QLabel("Filename Prefix:"))
        save_layout.addWidget(self.le_prefix)
        
        self.le_suffix = QLineEdit(self.settings.value("save/suffix", ""))
        save_layout.addWidget(QLabel("Filename Suffix:"))
        save_layout.addWidget(self.le_suffix)
        
        self.cb_csv = QCheckBox("Extract .csv file")
        self.cb_csv.setChecked(self.settings.value("save/csv_enabled", True, type=bool))
        save_layout.addWidget(self.cb_csv)
        
        self.le_csv_filename = QLineEdit(self.settings.value("save/csv_filename", "detection.csv"))
        save_layout.addWidget(QLabel("CSV Filename:"))
        save_layout.addWidget(self.le_csv_filename)
        
        # --- Advanced Settings Tab ---
        advanced_layout = QVBoxLayout(self.advanced_tab)
        advanced_layout.setAlignment(Qt.AlignTop)
        advanced_layout.setSpacing(5)
        self.le_leaf_threshold = QLineEdit(self.settings.value("advanced/leaf_threshold", "0.8"))
        self.le_leaf_threshold.setMaximumWidth(50)
        advanced_layout.addWidget(QLabel("Leaf Confidence Threshold:"))
        advanced_layout.addWidget(self.le_leaf_threshold)
        
        self.le_spot_threshold = QLineEdit(self.settings.value("advanced/spot_threshold", "0.3"))
        self.le_spot_threshold.setMaximumWidth(50)
        advanced_layout.addWidget(QLabel("Spot Confidence Threshold:"))
        advanced_layout.addWidget(self.le_spot_threshold)
        
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(dialog_buttons)
        
    def update_label_settings(self):
        """If both leaf and spot labels are unchecked, disable Count and Percentage."""
        if not (self.cb_show_leaf_label.isChecked() or self.cb_show_spot_label.isChecked()):
            self.cb_show_count.setChecked(False)
            self.cb_show_count.setEnabled(False)
            self.cb_show_percent.setChecked(False)
            self.cb_show_percent.setEnabled(False)
        else:
            self.cb_show_count.setEnabled(True)
            self.cb_show_percent.setEnabled(True)
    
    def update_graph_settings(self):
        """If Show Bounding Box is unchecked, disable Show Label and Show Confidence."""
        if not self.cb_show_box.isChecked():
            self.cb_show_label.setChecked(False)
            self.cb_show_conf.setChecked(False)
            self.cb_show_label.setEnabled(False)
            self.cb_show_conf.setEnabled(False)
        else:
            self.cb_show_label.setEnabled(True)
            self.cb_show_conf.setEnabled(True)
    
    def browse_save_path(self):
        """Open a directory dialog to choose the save folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if folder:
            self.le_save_path.setText(folder)
            
    def accept(self):
        """Save all settings to QSettings and close the dialog."""
        self.settings.setValue("view/show_leaf", self.cb_show_leaf_label.isChecked())
        self.settings.setValue("view/show_spot", self.cb_show_spot_label.isChecked())
        self.settings.setValue("view/show_count", self.cb_show_count.isChecked())
        self.settings.setValue("view/show_percent", self.cb_show_percent.isChecked())
        self.settings.setValue("view/show_box", self.cb_show_box.isChecked())
        self.settings.setValue("view/show_label", self.cb_show_label.isChecked())
        self.settings.setValue("view/show_conf", self.cb_show_conf.isChecked())
        
        self.settings.setValue("save/save_path", self.le_save_path.text())
        self.settings.setValue("save/prefix", self.le_prefix.text())
        self.settings.setValue("save/suffix", self.le_suffix.text())
        self.settings.setValue("save/csv_enabled", self.cb_csv.isChecked())
        self.settings.setValue("save/csv_filename", self.le_csv_filename.text())
        
        self.settings.setValue("advanced/leaf_threshold", self.le_leaf_threshold.text())
        self.settings.setValue("advanced/spot_threshold", self.le_spot_threshold.text())
        super().accept()

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        """Dialog displaying help information."""
        super().__init__(parent)
        self.setWindowTitle("Help")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(5)
        help_label = QLabel(
            "Instructions:\n"
            "1. Load images using 'Open File' or 'Open Folder'.\n"
            "2. Click 'Run' to perform detection on loaded images.\n"
            "3. Predicted result images and .csv report would be saved after running."
        )
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        """Dialog displaying about information including developers and copyright."""
        super().__init__(parent)
        self.setWindowTitle("About")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(5)
        about_text = (
            "OSU Leaf Spot Detector\n\n"
            "Developed by:\n"
            " - Heechan Jeong, Oregon State University\n"
            " - Heesung Woo, Oregon State University\n\n"
            "© 2025 Advanced Forestry Systems Lab. All rights reserved."
        )
        label = QLabel(about_text)
        label.setWordWrap(True)
        layout.addWidget(label)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class MainWindow(QMainWindow):
    def __init__(self):
        """Main application window initialization."""
        super().__init__()
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            current_dir = os.getcwd()
        logo_dir = os.path.join(current_dir, "logo")
        model_dir = os.path.join(current_dir, "model")
        self.setWindowTitle("OSU Leaf Spot Detector")
        self.setWindowIcon(QIcon(os.path.join(logo_dir, "main_icon.png")))
        self.settings = QSettings("YourCompany", "OSULeafSpotDetector")
        model_path = os.path.join(model_dir, "leafspot.pt")
        self.pred_model = YOLO(model_path)
        self.running = False
        self.abort = False
        self.save_dir = ""
        self.prefix = ""
        self.suffix = ""
        self.conf = 0.3
        self.imgsz = 1280
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)
        self.list_widget = CustomListWidget()
        self.list_widget.setFixedWidth(150)
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemClicked.connect(self.show_selected_image)
        top_layout.addWidget(self.list_widget)
        image_grid = QGridLayout()
        top_layout.addLayout(image_grid)
        self.label_original = QLabel("Original Image")
        self.label_original.setFixedSize(600, 600)
        self.label_original.setAlignment(Qt.AlignCenter)
        self.label_original.setStyleSheet("border: 1px solid black;")
        image_grid.addWidget(self.label_original, 0, 0)
        self.label_result = QLabel("Predicted Result")
        self.label_result.setFixedSize(600, 600)
        self.label_result.setAlignment(Qt.AlignCenter)
        self.label_result.setStyleSheet("border: 1px solid black;")
        image_grid.addWidget(self.label_result, 0, 1)
        bottom_layout = QHBoxLayout()
        main_layout.addLayout(bottom_layout)
        self.btn_open_file = QPushButton("Open File")
        self.btn_open_file.setToolTip("Open File")
        self.btn_open_file.setIcon(qta.icon('ei.file-new', color='green'))
        self.btn_open_file.setIconSize(QSize(32, 32))
        self.btn_open_file.setFixedSize(120, 50)
        self.btn_open_file.clicked.connect(self.open_file)
        bottom_layout.addWidget(self.btn_open_file)
        self.btn_open_folder = QPushButton("Open Folder")
        self.btn_open_folder.setToolTip("Open Folder")
        self.btn_open_folder.setIcon(qta.icon('mdi.folder-open-outline', color='green'))
        self.btn_open_folder.setIconSize(QSize(32, 32))
        self.btn_open_folder.setFixedSize(120, 50)
        self.btn_open_folder.clicked.connect(self.open_folder)
        bottom_layout.addWidget(self.btn_open_folder)
        self.btn_run = QPushButton("Run")
        self.btn_run.setToolTip("Run")
        self.btn_run.setIcon(qta.icon('ph.play-circle-bold', color='blue'))
        self.btn_run.setIconSize(QSize(32, 32))
        self.btn_run.setFixedSize(120, 50)
        self.btn_run.clicked.connect(self.run_model)
        bottom_layout.addWidget(self.btn_run)
        bottom_layout.addStretch()
        self.logo1 = QLabel()
        logo1_pixmap = QPixmap(os.path.join(logo_dir, "AFSL_logo.png"))
        logo1_pixmap = logo1_pixmap.scaled(220, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo1.setPixmap(logo1_pixmap)
        bottom_layout.addWidget(self.logo1)
        self.logo2 = QLabel()
        logo2_pixmap = QPixmap(os.path.join(logo_dir, "OSU_logo.png"))
        logo2_pixmap = logo2_pixmap.scaled(150, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo2.setPixmap(logo2_pixmap)
        bottom_layout.addWidget(self.logo2)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        self.current_image_path = None
        
        # Menubar order: Settings, Help, About
        menubar = self.menuBar()
        settings_action = menubar.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)
        help_action = menubar.addAction("Help")
        help_action.triggered.connect(self.show_help)
        about_action = menubar.addAction("About")
        about_action.triggered.connect(self.show_about)
    
    def open_file(self):
        """Open file dialog to select image files and add them to the list widget."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Images",
            "",
            "Images (*.png *.jpg *.tif *.bmp *.gif )"
        )
        if files:
            for f in files:
                exists = False
                for i in range(self.list_widget.count()):
                    if self.list_widget.item(i).data(Qt.UserRole) == f:
                        exists = True
                        break
                if not exists:
                    item = QListWidgetItem()
                    widget = ListItemWidget(os.path.basename(f))
                    item.setData(Qt.UserRole, f)
                    self.list_widget.addItem(item)
                    self.list_widget.setItemWidget(item, widget)
    
    def open_folder(self):
        """Open folder dialog, list image files in the folder, and add them to the list widget."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.list_widget.clear()
            allowed_extensions = (".jpg", ".png", ".gif", ".bmp", ".tif", ".jpeg")
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(allowed_extensions)]
            for f in files:
                item = QListWidgetItem()
                widget = ListItemWidget(os.path.basename(f))
                item.setData(Qt.UserRole, f)
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)
    
    def show_selected_image(self, item):
        """Display the selected image in the original image label."""
        image_path = item.data(Qt.UserRole)
        self.current_image_path = image_path
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(self.label_original.size(), Qt.KeepAspectRatio)
        self.label_original.setPixmap(scaled_pixmap)
    
    def run_model(self):
        """Run the detection model on all images in the list and display/save results."""
        if self.list_widget.count() == 0:
            QMessageBox.warning(self, "Warning", "Please load a file or folder before running the model.")
            return

        if self.running:
            self.abort = True
            return

        dialog = SaveSettingsDialog(self)
        if dialog.exec_() == QDialog.Rejected:
            return
        self.save_dir, self.prefix, self.suffix, csv_enabled, csv_filename = dialog.get_values()
        if not self.save_dir:
            QMessageBox.warning(self, "Warning", "You must specify a save directory.")
            return

        show_box = self.settings.value("view/show_box", False, type=bool)
        show_label = self.settings.value("view/show_label", False, type=bool)
        show_conf = self.settings.value("view/show_conf", False, type=bool)
        show_leaf = self.settings.value("view/show_leaf", True, type=bool)
        show_spot = self.settings.value("view/show_spot", True, type=bool)
        show_count = self.settings.value("view/show_count", True, type=bool)
        show_percent = self.settings.value("view/show_percent", True, type=bool)
        
        self.running = True
        self.abort = False
        self.btn_run.setText("Abort")
        self.btn_run.setIcon(qta.icon('ri.stop-circle-line', color='red'))
        total = self.list_widget.count()
        self.progress_bar.setMaximum(total)
        csv_data = []
        leaf_threshold = float(self.settings.value("advanced/leaf_threshold", "0.8"))
        spot_threshold = float(self.settings.value("advanced/spot_threshold", "0.3"))
        text_color = (0, 255, 0)
        bg_color = (0, 0, 0)
        for i in range(total):
            if self.abort:
                break
            item = self.list_widget.item(i)
            image_path = item.data(Qt.UserRole)
            self.current_image_path = image_path
            self.show_selected_image(item)
            QApplication.processEvents()
            results = self.pred_model(image_path, conf=self.conf, imgsz=self.imgsz)
            if not results:
                self.label_result.setText("No result returned.")
                leaf_pixels = 0
                spot_pixels = 0
                spot_percentage = 0
                spot_number = 0
            else:
                result = results[0]
                boxes = result.boxes
                masks = result.masks
                if boxes is not None and len(boxes) > 0:
                    keep_indices = []
                    for j, box in enumerate(boxes):
                        cls_id = int(box.cls.cpu().numpy()[0])
                        conf_val = float(box.conf.cpu().numpy()[0])
                        if (cls_id == 0 and conf_val >= leaf_threshold) or (cls_id == 1 and conf_val >= spot_threshold):
                            keep_indices.append(j)
                    if keep_indices:
                        result.boxes = boxes[keep_indices]
                        if masks is not None:
                            result.masks.data = masks.data[keep_indices]
                    else:
                        result.boxes = None
                        result.masks = None
                boxes = result.boxes
                masks = result.masks
                annotated_img = result.plot(boxes=show_box, labels=show_label, conf=show_conf)
                h, w = annotated_img.shape[:2]
                scale = self.imgsz / max(w, h)
                new_width = int(w * scale)
                new_height = int(h * scale)
                annotated_img_resized = cv2.resize(annotated_img, (new_width, new_height))
                counts = {}
                class_mask_acc = {}
                if boxes is not None:
                    for j, box in enumerate(boxes):
                        cls_id = int(box.cls.cpu().numpy()[0])
                        counts[cls_id] = counts.get(cls_id, 0) + 1
                        if masks is not None and j < len(masks.data):
                            mask_np = masks.data[j].cpu().numpy()
                            binary_mask = mask_np > 0.5
                            if cls_id not in class_mask_acc:
                                class_mask_acc[cls_id] = np.zeros_like(binary_mask, dtype=np.uint8)
                            class_mask_acc[cls_id] += binary_mask.astype(np.uint8)
                areas = {cls_id: np.count_nonzero(acc_mask == 1)
                         for cls_id, acc_mask in class_mask_acc.items()}
                leaf_pixels = areas.get(0, 0)
                spot_pixels = areas.get(1, 0)
                spot_percentage = (spot_pixels / leaf_pixels * 100) if leaf_pixels > 0 else 0
                spot_number = counts.get(1, 0)
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1
                font_thickness = 2
                x_position = 10
                y_position = 30
                if show_leaf:
                    class_name = self.pred_model.names[0]
                    text_line = f"{class_name} Area: {leaf_pixels} pixels"
                    (text_width, text_height), _ = cv2.getTextSize(text_line, font, font_scale, font_thickness)
                    top_left = (x_position - 5, y_position - text_height - 5)
                    bottom_right = (x_position + text_width + 5, y_position + 5)
                    cv2.rectangle(annotated_img_resized, top_left, bottom_right, bg_color, thickness=-1)
                    cv2.putText(annotated_img_resized, text_line, (x_position, y_position),
                                font, font_scale, text_color, font_thickness, cv2.LINE_AA)
                    y_position += text_height + 15
                if show_spot:
                    class_name = self.pred_model.names[1]
                    text_line = f"{class_name} Area: {spot_pixels} px"
                    if show_percent:
                        text_line += f" ({round(spot_percentage,2)}%)"
                    if show_count:
                        text_line += f", Count: {spot_number}"
                    (text_width, text_height), _ = cv2.getTextSize(text_line, font, font_scale, font_thickness)
                    top_left = (x_position - 5, y_position - text_height - 5)
                    bottom_right = (x_position + text_width + 5, y_position + 5)
                    cv2.rectangle(annotated_img_resized, top_left, bottom_right, bg_color, thickness=-1)
                    cv2.putText(annotated_img_resized, text_line, (x_position, y_position),
                                font, font_scale, text_color, font_thickness, cv2.LINE_AA)
                    y_position += text_height + 15
                orig_filename = os.path.basename(image_path)
                name, ext = os.path.splitext(orig_filename)
                new_filename = f"{self.prefix}_{name}"
                if self.suffix.strip():
                    new_filename += f"_{self.suffix}"
                new_filename += f"{ext}"
                os.makedirs(self.save_dir, exist_ok=True)
                save_path = os.path.join(self.save_dir, new_filename)
                cv2.imwrite(save_path, annotated_img_resized)
                if os.path.exists(save_path):
                    pixmap_result = QPixmap(save_path)
                    scaled_pixmap_result = pixmap_result.scaled(
                        self.label_result.size(), Qt.KeepAspectRatio
                    )
                    self.label_result.setPixmap(scaled_pixmap_result)
                else:
                    self.label_result.setText("Prediction failed or file not found.")
            csv_data.append([os.path.basename(image_path), leaf_pixels, spot_pixels, round(spot_percentage,2), spot_number])
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
            widget = self.list_widget.itemWidget(item)
            if widget:
                widget.show_check()
        if csv_enabled:
            if not os.path.isabs(csv_filename):
                csv_path = os.path.join(self.save_dir, csv_filename)
            else:
                csv_path = csv_filename
            with open(csv_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Image Name", "Leaf pixels", "Spot pixels", "Necrotic area (%)", "# of spots"])
                writer.writerows(csv_data)
        self.running = False
        self.abort = False
        self.btn_run.setText("Run")
        self.btn_run.setIcon(qta.icon('fa.play', color='blue'))
        QMessageBox.information(self, "Completed", "All tasks are completed.")
    
    def show_help(self):
        """Open the help dialog."""
        dialog = HelpDialog(self)
        dialog.exec_()
    
    def show_about(self):
        """Open the about dialog."""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def open_settings(self):
        """Open the settings dialog to adjust view, save, and advanced options."""
        dialog = SettingsDialog(self)
        dialog.exec_()
    
    def closeEvent(self, event):
        """Confirm exit when closing the main window."""
        reply = QMessageBox.question(self, "Exit", "Do you want to exit OSU Leaf Spot Detector?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.running:
                self.abort = True
            event.accept()
        else:
            event.ignore()

def main():
    """Application entry point."""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
