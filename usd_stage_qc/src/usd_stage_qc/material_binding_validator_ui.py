import os
from importlib import reload

import hou
from PySide6 import QtWidgets, QtCore, QtGui
from pxr import Usd

from usd_stage_qc import usd, houdini, trie_search, status_messages

for module in (usd, houdini, status_messages, trie_search):
    reload(module)


class MaterialBindingChecker(QtWidgets.QDialog):
    """UI widget to check missing materials and assign them on a Houdini USD stage."""

    def __init__(self, parent=None):
        """
        Initialize the material binding checker UI.

        Args:
            parent: Parent widget.
        """
        super(MaterialBindingChecker, self).__init__(parent=parent)
        self.stage_path = houdini.get_single_selected_node().path()
        self.stage = hou.node(self.stage_path).stage()
        self.assign_mat_node = None
        self.mat_binds = []
        self.searching = False

        self.resize(1000, 800)
        self.setWindowTitle('USD Material Binding Validator')
        self.central_layout = QtWidgets.QVBoxLayout()
        self.central_layout.setAlignment(QtCore.Qt.AlignTop)

        # Add splitter inside a search group
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.central_layout.addWidget(self.splitter)

        # _____________________________________________
        # Prim group box (left) Add prim group layout
        self.prim_list_grp = QtWidgets.QGroupBox("Prims")
        self.prim_list_layout = QtWidgets.QVBoxLayout()
        self.prim_list_grp.setLayout(self.prim_list_layout)
        self.splitter.addWidget(self.prim_list_grp)

        # Add Search Line QLineEdit
        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText('Search prim')
        self.prim_list_layout.addWidget(self.search_line)

        # Add Search Output QListWidget
        self.search_output = QtWidgets.QListWidget()
        self.search_output.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.search_output.setAlternatingRowColors(True)
        self.search_output.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.prim_list_layout.addWidget(self.search_output, stretch=1)

        # ______________________________________________________________
        # Prim details group box (right)
        self.prim_details_grp = QtWidgets.QGroupBox("Details")
        self.prim_details_layout = QtWidgets.QVBoxLayout()
        self.prim_details_grp.setLayout(self.prim_details_layout)
        self.splitter.addWidget(self.prim_details_grp)

        # Add Detail QFrame
        self.details_frame = QtWidgets.QFrame()
        self.details_frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.prim_details_layout.addWidget(self.details_frame, stretch=1)

        # Add QVBoxLayout to QFrame
        self.frame_layout = QtWidgets.QVBoxLayout()
        self.details_frame.setLayout(self.frame_layout)
        self.frame_layout.setAlignment(QtCore.Qt.AlignTop)

        # Add Prim Name Text Label QLabel
        self.prim_name_text_label = QtWidgets.QLabel("Prim Name:")
        self.frame_layout.addWidget(self.prim_name_text_label)

        # Add Prim Name Label QLabel
        self.prim_name_label = QtWidgets.QLabel()
        self.frame_layout.addWidget(self.prim_name_label)

        # Add Prim Path Text Label QLabel
        self.prim_path_text_label = QtWidgets.QLabel("\nPrim Path:")
        self.prim_path_text_label.setAlignment(QtCore.Qt.AlignLeft)
        self.frame_layout.addWidget(self.prim_path_text_label)

        # Add Prim Path Label QLabel
        self.prim_path_text = QtWidgets.QTextEdit()
        self.prim_path_text.setMaximumHeight(110)
        self.prim_path_text.setAlignment(QtCore.Qt.AlignLeft)
        self.frame_layout.addWidget(self.prim_path_text)

        # Add Prim Type Text Label QLabel
        self.prim_type_text_label = QtWidgets.QLabel("Prim Type:")
        self.prim_type_text_label.setAlignment(QtCore.Qt.AlignLeft)
        self.frame_layout.addWidget(self.prim_type_text_label)

        # Add Prim Type Label QLabel
        self.prim_type_label = QtWidgets.QLabel()
        self.prim_type_label.setAlignment(QtCore.Qt.AlignLeft)
        self.frame_layout.addWidget(self.prim_type_label)

        # Add Material Status Text Label

        self.mat_status_text_label = QtWidgets.QLabel("Material Status:")
        self.frame_layout.addWidget(self.mat_status_text_label)

        # Add Material Status Label
        self.mat_status_label = QtWidgets.QLabel()
        self.mat_status_label.setAlignment(QtCore.Qt.AlignLeft)
        self.frame_layout.addWidget(self.mat_status_label)

        # Add Prim Bound Label QLabel
        self.prim_bound_label = QtWidgets.QLabel("\nMaterial Bind:")
        self.prim_bound_label.setAlignment(QtCore.Qt.AlignLeft)
        self.frame_layout.addWidget(self.prim_bound_label)

        # Add Prim Bound Material Path Text
        self.prim_bound_path = QtWidgets.QTextEdit()
        self.prim_bound_path.setMaximumHeight(50)
        self.prim_bound_path.setAlignment(QtCore.Qt.AlignLeft)
        self.frame_layout.addWidget(self.prim_bound_path)

        # ___________________________________________
        # Add Assign grp
        self.assign_grp = QtWidgets.QGroupBox()
        self.assign_layout = QtWidgets.QVBoxLayout()
        self.assign_layout.setAlignment(QtCore.Qt.AlignBottom)
        self.assign_grp.setLayout(self.assign_layout)
        self.central_layout.addWidget(self.assign_grp)

        # Add Expand all QCheck Box

        self.expand_all_check = QtWidgets.QCheckBox("Expand All")
        self.assign_layout.addWidget(self.expand_all_check)

        # Add Materials Tree View

        self.tree_mat_list = QtWidgets.QTreeWidget(self)
        self.tree_mat_list.setHeaderLabels(["Material Libraries"])
        self.assign_layout.addWidget(self.tree_mat_list)

        # Add Bulk Assign QCheckBox
        self.bulk_assign_check = QtWidgets.QCheckBox("Bulk assign to all filtered primitives")
        self.assign_layout.addWidget(self.bulk_assign_check)

        # Add Assign Material button
        self.assign_mat_btn = QtWidgets.QPushButton("Assign")
        self.assign_layout.addWidget(self.assign_mat_btn)

        # Add Refresh button
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.assign_layout.addWidget(self.refresh_btn)

        # Fix splitter resizing and Size
        self.splitter.setSizes([self.width() // 2, self.width() // 2])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        # Add Styles:
        script_dir = os.path.dirname(__file__)
        resources_path = os.path.join(script_dir, "..", "..", "resources")
        resources_path = os.path.normpath(resources_path)

        with open(os.path.join(resources_path, "style_hou.qss"), 'r') as f:
            self.setStyleSheet(f.read())
        # _______________________________
        # On init functions call
        self.populate_material_tree()
        self.populate_prim_list()
        self.setLayout(self.central_layout)

        # _____________________________
        # Buttons connections
        self.search_output.itemSelectionChanged.connect(self.on_list_item_changed)
        self.assign_mat_btn.clicked.connect(self.on_assign_material_executed)
        self.refresh_btn.clicked.connect(self.on_refresh_executed)
        self.search_line.textEdited.connect(self.run_search)
        self.search_line.textChanged.connect(self.reset_search_state)
        self.expand_all_check.toggled.connect(self.on_expand_all_check)

    def populate_prim_list(self) -> None:
        """Populate the prim list with primitives missing material bindings."""
        self.search_output.clear()
        self.mat_binds = usd.check_live_houdini_stage(self.stage)

        for i in self.mat_binds:
            item = QtWidgets.QListWidgetItem(i.GetName())
            metadata = {
                'usd_prim': i,
            }
            item.setData(QtCore.Qt.UserRole, metadata)
            self.search_output.addItem(item)

    def get_selection(self, widget: QtWidgets.QAbstractItemView) \
            -> list[QtWidgets.QTreeWidgetItem | QtWidgets.QListWidgetItem] | None:
        """
        Return selected items from a list widget.

        Args:
            widget: List widget.
        """
        selected = widget.selectedItems()
        return selected if selected else None

    def on_list_item_changed(self) -> None:
        """Update detail view from selected item."""
        selected_items = self.get_selection(self.search_output)

        if selected_items is not None:
            last_selected = selected_items[-1]
            metadata = last_selected.data(QtCore.Qt.UserRole)
            usd_prim = metadata.get('usd_prim')
            self.populate_details_view(usd_prim)

    def populate_details_view(self, usd_prim: Usd.Prim) -> None:
        """
        Populate detail view from a USD prim.

        Args:
            usd_prim: USD prim.
        """
        if usd_prim:
            self.prim_name_label.setText(str(usd_prim.GetName()))
            path = str(usd_prim.GetPath())
            self.prim_path_text.setReadOnly(True)
            self.prim_path_text.setText(path)
            self.prim_type_label.setText(str(usd_prim.GetTypeName()))
            mat = usd.check_prim_material_binding(usd_prim)[0]
            self.mat_status_label.setText(
                str(usd.solve_material_status(mat))) if mat else self.mat_status_label.setText("None")
            self.prim_bound_path.setText(str(mat.GetPath())) if mat else self.prim_bound_path.setText('None')

    def on_refresh_executed(self) -> None:
        """Refresh prim list and clear details."""
        self.clear_details_view()
        self.populate_prim_list()
        self.search_line.clear()

    def clear_details_view(self) -> None:
        """Clear detail view."""
        self.prim_name_label.clear()
        self.prim_path_text.clear()
        self.prim_type_label.clear()
        self.mat_status_label.clear()
        self.prim_bound_path.clear()

    def populate_material_tree(self) -> None:
        """Populate material tree from stage materials."""
        self.tree_mat_list.clear()

        root = self.tree_mat_list.invisibleRootItem()
        materials = usd.find_all_materials(self.stage)

        for material in materials:
            path_str = str(material.GetPath())
            parts = path_str.strip('/').split('/')
            self.build_tree_recursive(root, parts, material)

    def build_tree_recursive(self, parent: QtWidgets.QListWidget, parts: list, material_prim: Usd.Prim) -> None:
        """
        Build tree structure from material paths.

        Args:
            parent: Parent tree item.
            parts: Path parts.
            material_prim: Material prim.
        """
        if not parts:
            return

        part = parts[0]
        found = None
        for i in range(parent.childCount()):
            if parent.child(i).text(0) == part:
                found = parent.child(i)
                break

        if found is None:
            found = QtWidgets.QTreeWidgetItem(parent)
            found.setText(0, part)
            metadata = {
                'usd_prim': material_prim,
            }
            found.setData(0, QtCore.Qt.UserRole, metadata)

        self.build_tree_recursive(found, parts[1:], material_prim)

    def on_expand_all_check(self) -> None:
        """Toggle expand state of material tree."""
        if self.expand_all_check.isChecked():
            self.tree_mat_list.expandAll()
        else:
            self.tree_mat_list.collapseAll()

    def on_assign_material_executed(self) -> None:
        """Assign selected material to primitives."""
        # Check if the selected material is valid and get its metadata
        selected_mat_item = self.get_selection(self.tree_mat_list)

        if selected_mat_item is not None:
            mat_metadata = selected_mat_item[0].data(0, QtCore.Qt.UserRole)
            material_prim = mat_metadata.get('usd_prim')
            if material_prim is None:
                status_messages.handle_error("The selected material is invalid."
                                             "Please select a valid material from the library.")
                return
        else:
            status_messages.handle_error("No material selected. "
                                         "Please select a material from the material library.")
        # Check if an Assign Material node already exists or needs to be created
        if self.assign_mat_node is None:
            self.create_assign_material_node()
            if self.assign_mat_node is None:
                status_messages.handle_error("Failed to create the Assign Material node. "
                                             "Ensure you are in a writable context.")
        #  If Bulk Assign is checked, selected_items is set to all filtered primitives
        if self.bulk_assign_check.isChecked():
            selected_items = [
                self.search_output.item(i)
                for i in range(self.search_output.count())
                if not self.search_output.item(i).isHidden()
            ]
        # Get the selection list if bulk selection is not checked
        else:
            selected_items = self.get_selection(self.search_output)

        if selected_items is not None:
            for item in selected_items:
                metadata = item.data(QtCore.Qt.UserRole)

                usd_prim = metadata.get('usd_prim')
                if usd_prim is None:
                    status_messages.handle_error("The selected geometry is invalid."
                                                 "Please select a valid geometry primitive.")

                # Get the number of materials already existing in material assign and populate assign material parameters
                new_mat_index = houdini.compute_mat_assign_index(self.assign_mat_node)
                houdini.populate_mat_assign_parms(self.assign_mat_node, new_mat_index, usd_prim, material_prim)

            # Set selection on the first visible item in a list if the bulk assign is checked
            if self.bulk_assign_check.isChecked():
                for i in range(self.search_output.count()):
                    item = self.search_output.item(i)
                    if not item.isHidden():
                        self.search_output.setCurrentItem(item)
                        item.setSelected(True)

                        break
            if self.get_selection(self.search_output):
                self.mat_status_label.setText(str(usd.solve_material_status(
                    material_prim))) if material_prim else self.mat_status_label.setText("None")
                self.prim_bound_path.setText(str(material_prim.GetPath()))

        else:
            status_messages.handle_error("No geometry selected. Please select a primitive from the list.")
            return
        self.search_output.clearSelection()

    def create_assign_material_node(self) -> None:
        """Create or reuse assign material node."""
        selected_node = hou.node(self.stage_path)

        if not selected_node:
            status_messages.handle_error("No node selected.")

        if selected_node.type().name() == "assignmaterial":
            self.assign_mat_node = selected_node
            return

        for output_node in selected_node.outputs():
            if output_node.type().name() == "assignmaterial":
                self.assign_mat_node = output_node
                break

        if not self.assign_mat_node:
            self.assign_mat_node = houdini.create_and_insert_hou_node(selected_node,
                                                                      "assignmaterial",
                                                                      "fix_missing_binding")

    def run_search(self) -> None:
        """Filter prim list using search input."""
        if not self.searching and self.search_line.text():
            self.clear_details_view()
            self.search_output.clearSelection()
            self.searching = True

        search_text = self.search_line.text().lower()

        trie = trie_search.Trie()

        list_items = []
        for index in range(self.search_output.count()):
            item = self.search_output.item(index)
            list_items.append(item)

        for prim in list_items:
            trie.insert(prim.text().lower())

        search_results = set(trie.autocomplete(search_text))

        for index in range(self.search_output.count()):
            item = self.search_output.item(index)

            if item.text().lower() in search_results or self.search_line.text() == '':
                item.setHidden(False)
            else:
                item.setHidden(True)

    def reset_search_state(self, text) -> None:
        """
        Reset search state when input is cleared.

        Args:
            text: Search text.
        """
        if not text:
            self.searching = False
            self.search_output.clearSelection()


dialog = None


def show_houdini() -> QtWidgets.QDialog:
    """Launch the material binding checker UI."""
    import hou
    global dialog
    dialog = MaterialBindingChecker(parent=hou.qt.mainWindow())
    dialog.show()
    return dialog
