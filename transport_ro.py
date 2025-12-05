import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                               QGroupBox, QMessageBox, QSpinBox)
from PySide6.QtCore import Qt
from gurobipy import Model, GRB, quicksum


class TransportApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Problème de Transport - Projet RO")
        self.resize(700, 650)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Instructions pour l'utilisateur
        instructions = QLabel(
            "Saisir les coûts dans le tableau ci-dessous, puis les offres et demandes. "
            "Cliquez sur 'Résoudre' pour calculer le coût minimal."
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        # Section dimension dynamique pour choisir le nombre de sources et destinations
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(QLabel("Nombre de sources :"))
        self.n_sources_spin = QSpinBox()
        self.n_sources_spin.setValue(3)
        self.n_sources_spin.setMinimum(1)
        self.n_sources_spin.valueChanged.connect(self.update_tables)
        dim_layout.addWidget(self.n_sources_spin)

        dim_layout.addWidget(QLabel("Nombre de destinations :"))
        self.n_dest_spin = QSpinBox()
        self.n_dest_spin.setValue(3)
        self.n_dest_spin.setMinimum(1)
        self.n_dest_spin.valueChanged.connect(self.update_tables)
        dim_layout.addWidget(self.n_dest_spin)

        main_layout.addLayout(dim_layout)

        # Tableaux des données
        self.cost_table = QTableWidget()
        self.offre_table = QTableWidget()
        self.demande_table = QTableWidget()
        self.result_table = QTableWidget()

        self.update_tables()  # initialise les tableaux

        # Bouton résoudre
        self.solve_button = QPushButton("Résoudre")
        self.solve_button.clicked.connect(self.solve_transport)
        main_layout.addWidget(self.solve_button, alignment=Qt.AlignCenter)

        # Résultat
        self.result_label = QLabel("Coût total minimal : ")
        self.result_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.result_label)

        # Style global
        self.setStyleSheet("""
            QGroupBox { font-weight: bold; margin-top: 10px; }
            QLabel { font-size: 14px; }
            QTableWidget { gridline-color: gray; }
            QHeaderView::section { background-color: #404040; color: white; }
            QPushButton { font-size: 14px; padding: 5px; }
        """)

    def update_tables(self):
        n_sources = self.n_sources_spin.value()
        n_dest = self.n_dest_spin.value()

        # --- Coûts ---
        self._setup_table(self.cost_table, n_sources, n_dest, "Coûts", row_prefix="S", col_prefix="D")

        # --- Offres ---
        self._setup_table(self.offre_table, n_sources, 1, "Offres des sources", row_prefix="S", col_prefix="")

        # --- Demandes ---
        self._setup_table(self.demande_table, 1, n_dest, "Demandes des destinations", row_prefix="", col_prefix="D")

        # --- Résultats ---
        self._setup_table(self.result_table, n_sources, n_dest, "Solution Optimale", row_prefix="S", col_prefix="D", editable=False)

    def _setup_table(self, table, rows, cols, title, row_prefix="", col_prefix="", editable=True):
        group_box = QGroupBox(title)
        layout = QVBoxLayout()
        layout.addWidget(table)
        group_box.setLayout(layout)

        table.setRowCount(rows)
        table.setColumnCount(cols)
        table.setHorizontalHeaderLabels([f"{col_prefix}{j+1}" for j in range(cols)])
        table.setVerticalHeaderLabels([f"{row_prefix}{i+1}" for i in range(rows)])
        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnsToContents()
        table.setEditTriggers(QTableWidget.AllEditTriggers if editable else QTableWidget.NoEditTriggers)

        # Replace old group box in layout
        parent_layout = self.layout()
        for i in range(parent_layout.count()):
            widget = parent_layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox) and widget.title() == title:
                parent_layout.itemAt(i).widget().deleteLater()
                parent_layout.insertWidget(i, group_box)
                return
        parent_layout.addWidget(group_box)

    def solve_transport(self):
        try:
            n_sources = self.cost_table.rowCount()
            n_dest = self.cost_table.columnCount()

            # Lecture des données
            couts = self._read_table(self.cost_table, n_sources, n_dest)
            offres = [row[0] for row in self._read_table(self.offre_table, n_sources, 1)]
            demandes = self._read_table(self.demande_table, 1, n_dest)[0]

            # Modèle Gurobi
            m = Model("Transport")
            x = {(i, j): m.addVar(vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
                 for i in range(n_sources) for j in range(n_dest)}

            m.setObjective(quicksum(couts[i][j] * x[i, j] for i in range(n_sources) for j in range(n_dest)), GRB.MINIMIZE)

            for i in range(n_sources):
                m.addConstr(quicksum(x[i, j] for j in range(n_dest)) <= offres[i])
            for j in range(n_dest):
                m.addConstr(quicksum(x[i, j] for i in range(n_sources)) >= demandes[j])

            m.optimize()

            if m.status == GRB.OPTIMAL:
                self.result_label.setText(f"Coût total minimal : {m.objVal:.2f}")
                for i in range(n_sources):
                    for j in range(n_dest):
                        item = QTableWidgetItem(f"{x[i, j].x:.2f}")
                        item.setTextAlignment(Qt.AlignCenter)
                        self.result_table.setItem(i, j, item)
            else:
                QMessageBox.warning(self, "Résultat", "Aucune solution optimale trouvée.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la résolution : {e}")

    @staticmethod
    def _read_table(table, rows, cols):
        data = []
        for i in range(rows):
            row = []
            for j in range(cols):
                item = table.item(i, j)
                value = float(item.text()) if item and item.text() else 0
                row.append(value)
            data.append(row)
        return data


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransportApp()
    window.show()
    sys.exit(app.exec())
