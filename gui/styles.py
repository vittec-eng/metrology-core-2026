STYLE_SHEET = """
/* ==================== TEMA OSCURO ESTILO VS CODE ==================== */

/* ==================== TEMA OSCURO ESTILO VS CODE ==================== */
QMainWindow {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

/* ==================== APLICACIÓN PRINCIPAL ==================== */
QWidget {
    background-color: #252526;
    color: #d4d4d4;
}

/* ==================== BARRAS Y SEPARADORES ==================== */
QMenuBar {
    background-color: #252526;
    color: #e0e0e0;
    border-bottom: 1px solid #3e3e42;
}

QMenuBar::item:selected {
    background-color: #3e3e42;
    color: white;
}

/* ==================== BOTONES ==================== */
QPushButton {
}

QPushButton#ElementBtn {
    background-color: #3e3e42;
    color: #d4d4d4;
    border: 1px solid #5e5e62;
    border-radius: 4px;
    padding: 8px 12px;
    text-align: left;
    font-size: 11px;
}

QPushButton#ElementBtn:hover {
    background-color: #4e4e52;
    border: 1px solid #6e6e72;
}

QPushButton#ElementBtn:pressed {
    background-color: #2e2e32;
    border: 1px solid #4e4e52;
}

QPushButton#ActionBtn {
    background-color: #0078d7;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11px;
}

QPushButton#ActionBtn:hover {
    background-color: #106ebe;
}

QPushButton#ActionBtn:pressed {
    background-color: #005a9e;
}

QPushButton#VolverBtn {
    background-color: #0078d7;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11px;
}

QPushButton#VolverBtn:hover {
    background-color: #106ebe;
}

QPushButton#VolverBtn:pressed {
    background-color: #005a9e;
}

QPushButton#WrapperBtn {
    background-color: #252525;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
    margin-bottom: 6px;
    text-align: left;
    padding: 10px;
}

QPushButton#WrapperBtn:hover {
    background-color: #2d2d2d;
    border: 1px solid #0078d7; /* Azul por defecto */
}

QPushButton#WrapperBtn:pressed {
    background-color: #1a1a1a;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6e6e70;
}

/* ==================== COMBOS ==================== */
QComboBox {
    background-color: #3e3e42;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px;
    font-size: 11px;
}

QComboBox:focus {
    border: 2px solid #0078d7;
    background-color: #2d2d30;
}

/* ==================== SPIN BOX ==================== */
QSpinBox {
    background-color: #252526;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    padding: 8px;
    padding-right: 20px;
    color: #d4d4d4;
    font-size: 13px;
}

QSpinBox:focus {
    border: 1px solid #0078d4;
}

/* BOTONES - mismos colores que el fondo principal */
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    background: #252526;
    border-left: 1px solid #3e3e42;
}

QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    background: #252526;
    border-left: 1px solid #3e3e42;
}

/* FLECHAS */
QSpinBox::up-arrow {
    width: 7px;
    height: 7px;
}

QSpinBox::down-arrow {
    width: 7px;
    height: 7px;
}

/* ==================== DIALOGS Y VENTANAS ==================== */
QDialog {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QMessageBox {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QMessageBox QLabel {
    color: #e0e0e0;
}

QMessageBox QPushButton {
    min-width: 60px;
}

/* ==================== ÁREAS DE TEXTO ==================== */
QTextEdit, QPlainTextEdit {
    background-color: #0a0a0a;
    color: #888888;
    border: 1px solid #2a2a2a;
}

/* ==================== TREE VIEW ==================== */
QTreeView {
    background-color: #0f0f0f;
    color: #888888;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
}

QTreeView::item:selected {
    background-color: #0078d7;
    color: white;
}

QTreeView::item:hover {
    background-color: #1a1a1a;
}

/* ==================== DOCK WIDGETS ==================== */
QDockWidget {
    color: #e0e0e0;
    titlebar-close-icon: none;
}

QDockWidget::title {
    background-color: #2d2d30;
    color: #e0e0e0;
    padding: 5px;
    border: 1px solid #3e3e42;
}

/* ==================== SPLITTER ==================== */
QSplitter::handle {
    background-color: #3e3e42;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #0078d7;
}

/* ==================== FRAME ==================== */
QFrame {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QFrame#PlainFrame {
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    border-radius: 4px;
}

/* ==================== SCROLL AREA ==================== */
QScrollArea {
    background-color: #1e1e1e;
    border: none;
}
"""