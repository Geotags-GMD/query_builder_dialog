import os
import json
from qgis.core import QgsProject
from qgis.PyQt import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox


class QueryBuilderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Query Builder and Manager")

        # Initialize fields and values lists
        self.fields = []
        self.values = []

        # Create Tab Widget
        self.tabs = QtWidgets.QTabWidget()

        # Create tab layouts
        self.query_builder_tab = QtWidgets.QWidget()
        self.query_list_tab = QtWidgets.QWidget()

        # Initialize queries dictionary
        self.queries = {}

        # Build tabs
        self.init_query_list_tab()
        self.init_query_builder_tab()

        # Add tabs to the main layout (Query List first, Query Builder second)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # Load saved queries and populate the list
        self.load_saved_queries()

        # Populate layers in the query builder tab
        self.populate_layers()

    def init_query_builder_tab(self):
        """Initialize the query builder tab UI."""
        layout = QtWidgets.QVBoxLayout()

        # Layer selection dropdown
        self.layer_dropdown = QtWidgets.QComboBox()
        self.layer_dropdown.currentIndexChanged.connect(self.populate_fields)  # Connect to field population

        # Fields search and dropdown
        self.field_search = QtWidgets.QLineEdit()
        self.field_search.setPlaceholderText("Search Fields")
        self.field_search.textChanged.connect(self.filter_fields)  # Connect to field filtering

        self.field_dropdown = QtWidgets.QComboBox()
        self.field_dropdown.currentIndexChanged.connect(self.populate_values)  # Populate values based on selected field

        # Values search and dropdown
        self.value_search = QtWidgets.QLineEdit()
        self.value_search.setPlaceholderText("Search Values")
        self.value_search.textChanged.connect(self.filter_values)  # Connect to value filtering

        self.value_dropdown = QtWidgets.QComboBox()

        # Operator dropdown
        self.operator_input = QtWidgets.QComboBox()
        self.operator_input.addItems(['=', '>', '<', '>=', '<=', '!=', 'LIKE'])

        # Query name input
        self.query_name_input = QtWidgets.QLineEdit()

        # Button to add query
        self.btn_add_query = QtWidgets.QPushButton("Add Query")
        self.btn_add_query.clicked.connect(self.add_or_update_query)

        # Button to test query (new feature)
        self.btn_test_query = QtWidgets.QPushButton("Test Query")
        self.btn_test_query.clicked.connect(self.test_query)

        # Add widgets to layout
        layout.addWidget(QtWidgets.QLabel("Select Layer:"))
        layout.addWidget(self.layer_dropdown)
        layout.addWidget(QtWidgets.QLabel("Search Fields:"))
        layout.addWidget(self.field_search)  # Search bar for fields
        layout.addWidget(QtWidgets.QLabel("Select Field:"))
        layout.addWidget(self.field_dropdown)
        layout.addWidget(QtWidgets.QLabel("Search Values:"))
        layout.addWidget(self.value_search)  # Search bar for values
        layout.addWidget(QtWidgets.QLabel("Select Value:"))
        layout.addWidget(self.value_dropdown)
        layout.addWidget(QtWidgets.QLabel("Operator:"))
        layout.addWidget(self.operator_input)
        layout.addWidget(QtWidgets.QLabel("Query Name:"))
        layout.addWidget(self.query_name_input)
        layout.addWidget(self.btn_add_query)
        layout.addWidget(self.btn_test_query)  # Add the test query button

        self.query_builder_tab.setLayout(layout)
        self.tabs.addTab(self.query_builder_tab, "Build Query")

    def init_query_list_tab(self):
        """Initialize the tab to display and apply pre-built queries."""
        layout = QtWidgets.QVBoxLayout()

        # List view to show queries
        self.query_list_view = QtWidgets.QListView()
        self.query_list_model = QtCore.QStringListModel()
        self.query_list_view.setModel(self.query_list_model)

        # Connect double-click event to load the query for editing
        self.query_list_view.doubleClicked.connect(self.load_query_for_editing)

        # Button to apply the selected query
        self.btn_apply_query = QtWidgets.QPushButton("Apply Selected Query")
        self.btn_apply_query.clicked.connect(self.apply_query)

        filter_button_layout = QtWidgets.QHBoxLayout()

        # Group of buttons for managing queries (delete, update, clear filter)
        self.btn_delete_query = QtWidgets.QPushButton("Delete")
        self.btn_delete_query.clicked.connect(self.delete_query)

        self.btn_update_query = QtWidgets.QPushButton("Update")
        self.btn_update_query.clicked.connect(self.open_update_dialog)  # Open the update dialog

        # Button to clear the filter (new feature)
        self.btn_clear_filter = QtWidgets.QPushButton("Clear")
        self.btn_clear_filter.clicked.connect(self.clear_filter)

        # Add widgets to layout
        layout.addWidget(QtWidgets.QLabel("Saved Queries:"))
        layout.addWidget(self.query_list_view)
        layout.addWidget(self.btn_apply_query)

        filter_button_layout.addWidget(self.btn_delete_query)  # Add the delete query button
        filter_button_layout.addWidget(self.btn_update_query)  # Add the update query button
        filter_button_layout.addWidget(self.btn_clear_filter)  # Add the clear filter button

        layout.addLayout(filter_button_layout)

        self.query_list_tab.setLayout(layout)
        self.tabs.addTab(self.query_list_tab, "Query List")

    def load_query_for_editing(self, index):
        """Load the selected query into the query builder for editing."""
        query_name = index.data()  # Get the name of the selected query
        query = self.queries.get(query_name, {})

        if query:
            # Parse the query expression (simplified for the basic operator case)
            expression = query['expression']
            # For example, 'field_name' = 'value'
            field, rest = expression.split(' ', 1)
            operator, value = rest.split(' ', 1)

            # Remove any surrounding quotes from the value
            value = value.strip("'")

            # Populate the query builder fields with the selected query's data
            self.field_dropdown.setCurrentText(field.strip('"'))
            self.operator_input.setCurrentText(operator)
            self.value_dropdown.setCurrentText(value)
            self.query_name_input.setText(query_name)

    def open_update_dialog(self):
        """Open the update dialog for editing the selected query."""
        selected_query_index = self.query_list_view.currentIndex()
        query_name = selected_query_index.data()

        if not query_name:
            QMessageBox.warning(self, "Error", "Please select a query to update.")
            return

        query = self.queries.get(query_name)
        if query:
            self.update_dialog = UpdateQueryDialog(query_name, query['expression'], self)
            self.update_dialog.query_updated.connect(self.update_query)
            self.update_dialog.exec_()

    def populate_layers(self):
        """Populate the list of available layers from the QGIS project."""
        layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
        self.layer_dropdown.addItems(layer_names)

    def populate_fields(self):
        """Populate the fields (attributes) for the selected layer."""
        self.field_dropdown.clear()
        self.fields = []  # Reset fields list
        selected_layer_name = self.layer_dropdown.currentText()
        layer = self.get_layer_by_name(selected_layer_name)
        
        if layer:
            # Get the fields from the selected layer
            self.fields = [field.name() for field in layer.fields()]
            self.field_dropdown.addItems(self.fields)
        else:
            self.field_dropdown.addItem("No layer selected")

    def populate_values(self):
        """Populate unique values for the selected field."""
        self.value_dropdown.clear()
        self.values = []  # Reset values list
        selected_layer_name = self.layer_dropdown.currentText()
        layer = self.get_layer_by_name(selected_layer_name)

        if layer:
            selected_field = self.field_dropdown.currentText()
            if selected_field and selected_field != "No layer selected":
                self.values = layer.uniqueValues(layer.fields().indexOf(selected_field))
                self.value_dropdown.addItems([str(value) for value in self.values])
            else:
                self.value_dropdown.addItem("No field selected")
        else:
            self.value_dropdown.addItem("No layer selected")

    def filter_fields(self):
        """Filter the fields in the dropdown based on the search input."""
        search_text = self.field_search.text().lower()
        if not hasattr(self, 'fields') or not self.fields:
            self.field_dropdown.clear()
            self.field_dropdown.addItem("No fields available")
            return

        filtered_fields = [field for field in self.fields if search_text in field.lower()]
        self.field_dropdown.clear()
        if filtered_fields:
            self.field_dropdown.addItems(filtered_fields)
        else:
            self.field_dropdown.addItem("No matching fields")

    def filter_values(self):
        """Filter the values in the dropdown based on the search input."""
        search_text = self.value_search.text().lower()
        if not hasattr(self, 'values') or not self.values:
            self.value_dropdown.clear()
            self.value_dropdown.addItem("No values available")
            return

        filtered_values = [str(value) for value in self.values if search_text in str(value).lower()]
        self.value_dropdown.clear()
        if filtered_values:
            self.value_dropdown.addItems(filtered_values)
        else:
            self.value_dropdown.addItem("No matching values")

    def get_layer_by_name(self, layer_name):
        """Get a layer by name."""
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == layer_name:
                return layer
        return None

    
    def add_or_update_query(self):
        """Add or update a query in the internal dictionary and automatically save to JSON."""
        field = self.field_dropdown.currentText()
        operator = self.operator_input.currentText()
        value = self.value_dropdown.currentText()
        query_name = self.query_name_input.text()

        if not field or not value or not query_name:
            QMessageBox.warning(self, "Error", "Please fill out all fields to create a query.")
            return

        # Build the query expression
        expression = f'"{field}" {operator} \'{value}\''

        # Store in queries dictionary
        self.queries[query_name] = {"expression": expression}

        self.update_query_list()  # Refresh the query list view
        self.save_queries()  # Save changes to JSON

        QMessageBox.information(self, "Success", f"Query '{query_name}' added/updated.")

        # Clear the input fields
        self.field_dropdown.setCurrentIndex(-1)  # Reset to no selection
        self.operator_input.setCurrentIndex(0)  # Reset to default operator
        self.value_dropdown.clear()  # Clear the values
        self.query_name_input.clear()  # Clear the query name input



    def update_query(self, query_name, expression):
        """Update the selected query's expression."""
        self.queries[query_name]['expression'] = expression
        self.update_query_list()  # Refresh the query list view
        self.save_queries()  # Save changes to JSON

    def delete_query(self):
        """Delete the selected query from the list."""
        selected_query_index = self.query_list_view.currentIndex()
        query_name = selected_query_index.data()

        if not query_name:
            QMessageBox.warning(self, "Error", "Please select a query to delete.")
            return

        del self.queries[query_name]
        self.update_query_list()  # Refresh the query list view
        self.save_queries()  # Save changes to JSON

        QMessageBox.information(self, "Success", f"Query '{query_name}' deleted.")

    def update_query_list(self):
        """Update the list view with the current queries."""
        self.query_list_model.setStringList(list(self.queries.keys()))

    def save_queries(self):
        """Save the queries to a JSON file."""
        plugin_dir = os.path.dirname(__file__)
        json_path = os.path.join(plugin_dir, "saved_queries.json")

        try:
            with open(json_path, "w") as json_file:
                json.dump({"queries": self.queries}, json_file, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save queries: {e}")

    def load_saved_queries(self):
        """Load saved queries from a JSON file."""
        plugin_dir = os.path.dirname(__file__)
        json_path = os.path.join(plugin_dir, "saved_queries.json")

        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as json_file:
                    data = json.load(json_file)
                    self.queries = data.get("queries", {})
                    self.update_query_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load saved queries: {e}")

    def apply_query(self):
        """Apply the selected query to the selected layer."""
        selected_layer_name = self.layer_dropdown.currentText()
        layer = self.get_layer_by_name(selected_layer_name)

        if not layer:
            QMessageBox.warning(self, "Error", "Please select a valid layer.")
            return

        selected_query_index = self.query_list_view.currentIndex()
        query_name = selected_query_index.data()

        if not query_name:
            QMessageBox.warning(self, "Error", "Please select a query to apply.")
            return

        query = self.queries.get(query_name, {})

        if query:
            expression = query.get("expression")
            layer.setSubsetString(expression)
            QMessageBox.information(self, "Success", f"Query '{query_name}' applied to layer '{selected_layer_name}'")

    def test_query(self):
        """Test the query without saving, by applying it to the selected layer."""
        selected_layer_name = self.layer_dropdown.currentText()
        layer = self.get_layer_by_name(selected_layer_name)

        if not layer:
            QMessageBox.warning(self, "Error", "Please select a valid layer.")
            return

        field = self.field_dropdown.currentText()
        operator = self.operator_input.currentText()
        value = self.value_dropdown.currentText()

        if not field or not value:
            QMessageBox.warning(self, "Error", "Please select a field and value.")
            return

        # Build the query expression
        expression = f'"{field}" {operator} \'{value}\''

        # Apply the query temporarily to the layer
        layer.setSubsetString(expression)
        QMessageBox.information(self, "Test Query", f"Query tested: {expression}")

    def clear_filter(self):
        """Clear any applied filters on the selected layer."""
        selected_layer_name = self.layer_dropdown.currentText()
        layer = self.get_layer_by_name(selected_layer_name)

        if layer:
            layer.setSubsetString("")  # Clear any filter applied to the layer
            QMessageBox.information(self, "Clear Filter", f"Filter cleared on layer '{selected_layer_name}'")


class UpdateQueryDialog(QtWidgets.QDialog):
    query_updated = QtCore.pyqtSignal(str, str)  # Signal to notify when a query is updated

    def __init__(self, query_name, expression, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Query")

        # Create UI elements for the update dialog
        layout = QtWidgets.QVBoxLayout()

        self.query_name_input = QtWidgets.QLineEdit(query_name)
        self.query_name_input.setReadOnly(True)  # Make the query name read-only

        self.expression_input = QtWidgets.QLineEdit(expression)

        # Button to confirm update
        self.btn_update_query = QtWidgets.QPushButton("Update Query")
        self.btn_update_query.clicked.connect(self.update_query)

        # Add widgets to layout
        layout.addWidget(QtWidgets.QLabel("Query Name:"))
        layout.addWidget(self.query_name_input)
        layout.addWidget(QtWidgets.QLabel("Expression:"))
        layout.addWidget(self.expression_input)
        layout.addWidget(self.btn_update_query)

        self.setLayout(layout)

    def update_query(self):
        """Emit the updated query signal."""
        updated_expression = self.expression_input.text()
        query_name = self.query_name_input.text()

        if updated_expression:
            self.query_updated.emit(query_name, updated_expression)  # Emit the signal with updated data
            self.accept()  # Close the dialog
        else:
            QMessageBox.warning(self, "Error", "Expression cannot be empty.")
