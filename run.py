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
    QLineEdit, QDialogButtonBox, QAbstractItemView, QMenu, QCheckBox
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize

from ultralytics import YOLO

class ListItemWidget(QWidget):
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        self.label = QLabel(filename)
        layout.addWidget(self.label)
        layout.addStretch()
        self.check_label = QLabel()
        layout.addWidget(self.check_label)
    
    def show_check(self):
        pixmap = qta.icon('fa.check', color='green').pixmap(16, 16)
        self.check_label.setPixmap(pixmap)

class CustomListWidget(QListWidget):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for item in self.selectedItems():
                self.takeItem(self.row(item))
        else:
            super().keyPressEvent(event)
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            for item in self.selectedItems():
                self.takeItem(self.row(item))

class SaveSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Settings")
        layout = QVBoxLayout(self)

        label_save_path = QLabel("Save Path")
        layout.addWidget(label_save_path)
        
        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("Select save directory")
        browse_button = QPushButton()
        browse_button.setIcon(qta.icon('fa.folder', color='orange'))
        browse_button.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_button)
        layout.addLayout(dir_layout)

        optional_label = QLabel("Optional")
        layout.addWidget(optional_label)

        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("Enter filename prefix")
        layout.addWidget(self.prefix_edit)

        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText("Enter filename suffix")
        layout.addWidget(self.suffix_edit)
        
        self.csv_checkbox = QCheckBox("Extract .csv file")
        self.csv_checkbox.setChecked(True)
        layout.addWidget(self.csv_checkbox)
        
        self.csv_edit = QLineEdit("detection.csv")
        layout.addWidget(self.csv_edit)
        
        self.csv_checkbox.toggled.connect(self.toggle_csv_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def toggle_csv_edit(self, checked):
        self.csv_edit.setEnabled(checked)
        
    def browse_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if folder:
            self.dir_edit.setText(folder)
            
    def get_values(self):
        return (self.dir_edit.text(), 
                self.prefix_edit.text(), 
                self.suffix_edit.text(), 
                self.csv_checkbox.isChecked(), 
                self.csv_edit.text())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            current_dir = os.getcwd()
        logo_dir = os.path.join(current_dir, "logo")
        model_dir = os.path.join(current_dir, "model")
        self.setWindowTitle("OSU Leaf Spot Detector")
        self.setWindowIcon(QIcon(os.path.join(logo_dir, "main_icon.png")))
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
        self.btn_run = QPushButton("Run Model")
        self.btn_run.setToolTip("Run Model")
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

    def open_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Images",
            "",
            "Images (*.png *.jpg *.tif *.bmp *.gif )"
        )
        if files:
            for f in files:
                exists = False
                # 중복 체크: 파일 경로 비교
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
        image_path = item.data(Qt.UserRole)
        self.current_image_path = image_path
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(self.label_original.size(), Qt.KeepAspectRatio)
        self.label_original.setPixmap(scaled_pixmap)

    def run_model(self):
        if self.list_widget.count() == 0:
            QMessageBox.warning(self, "Warning", "Please load a file or folder before running the model.")
            return

        if self.running:
            self.abort = True
            return
        dialog = SaveSettingsDialog(self)
        if dialog.exec_() == QDialog.Rejected:
            return
        # suffix 값도 받아옴
        self.save_dir, self.prefix, self.suffix, csv_enabled, csv_filename = dialog.get_values()
        if not self.save_dir:
            QMessageBox.warning(self, "Warning", "You must specify a save directory.")
            return
        self.running = True
        self.abort = False
        self.btn_run.setText("Abort")
        self.btn_run.setIcon(qta.icon('ri.stop-circle-line', color='red'))
        total = self.list_widget.count()
        self.progress_bar.setMaximum(total)
        csv_data = []
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
                        if (cls_id == 0 and conf_val >= 0.8) or (cls_id == 1 and conf_val >= 0.3):
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
                annotated_img = result.plot(boxes=False, labels=False, conf=False)
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
                for cls_id in counts:
                    class_name = self.pred_model.names[cls_id]
                    count = counts[cls_id]
                    if cls_id == 0:
                        text_line = f"{class_name} Area: {leaf_pixels} pixels"
                    else:
                        text_line = f"{class_name} Area: {spot_pixels} px ({round(spot_percentage,2)}%), Count: {count}"
                    (text_width, text_height), _ = cv2.getTextSize(text_line, font, font_scale, font_thickness)
                    top_left = (x_position - 5, y_position - text_height - 5)
                    bottom_right = (x_position + text_width + 5, y_position + 5)
                    cv2.rectangle(annotated_img_resized, top_left, bottom_right, (0, 0, 0), thickness=-1)
                    cv2.putText(annotated_img_resized, text_line, (x_position, y_position),
                                font, font_scale, (0, 255, 0), font_thickness, cv2.LINE_AA)
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
        self.btn_run.setText("Run Model")
        self.btn_run.setIcon(qta.icon('fa.play', color='blue'))
        QMessageBox.information(self, "Completed", "All tasks are completed.")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Exit", "Do you want to exit OSU Leaf Spot Detector?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.running:
                self.abort = True
            event.accept()
        else:
            event.ignore()

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
