import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from key_committing_tool import find_minimum_rounds, generate_equations, analyze_security, analyze_security_with_guessing

class KeyCommittingTool(QtWidgets.QMainWindow):
    def __init__(self):
        super(KeyCommittingTool, self).__init__()
        
        # Adjust the path to the UI file
        ui_path = os.path.join(os.path.dirname(__file__), 'key_committing_tool.ui')
        uic.loadUi(ui_path, self)

        self.scheme_defaults = {
            "AEGIS-128": {
                "num_block_types": "1",
                "num_blocks": "5",
                "block_names": "S",
                "num_ad_types": "1",
                "ad_counts": "1",
                "ad_names": "AD",
                "round_functions": "A(S4)+S0+AD0\nA(S0)+S1\nA(S1)+S2\nA(S2)+S3\nA(S3)+S4"
            },
            "AEGIS-128L": {
                "num_block_types": "1",
                "num_blocks": "8",
                "block_names": "S",
                "num_ad_types": "1",
                "ad_counts": "2",
                "ad_names": "AD",
                "round_functions": "A(S7)+S0+AD0\nA(S0)+S1\nA(S1)+S2\nA(S2)+S3\nA(S3)+S4+AD1\nA(S4)+S5\nA(S5)+S6\nA(S6)+S7"
            },
            "AEGIS-256": {
                "num_block_types": "1",
                "num_blocks": "6",
                "block_names": "S",
                "num_ad_types": "1",
                "ad_counts": "1",
                "ad_names": "AD",
                "round_functions": "A(S4)+S0+AD0\nA(S0)+S1\nA(S1)+S2\nA(S2)+S3\nA(S3)+S4\nA(S4)+S5"
            },
            "Rocca": {
                "num_block_types": "1",
                "num_blocks": "8",
                "block_names": "S",
                "num_ad_types": "1",
                "ad_counts": "2",
                "ad_names": "AD",
                "round_functions": "S7+AD0\nA(S0)+S7\nS1+S6\nA(S2)+S1\nS3+AD1\nA(S4)+S3\nA(S5)+S4\nS0+S6"
            },
            "Rocca-S": {
                "num_block_types": "1",
                "num_blocks": "7",
                "block_names": "S",
                "num_ad_types": "1",
                "ad_counts": "2",
                "ad_names": "AD",
                "round_functions": "S1+S6\nA(S0)+AD0\nA(S1)+S0\nA(S2)+S6\nA(S3)+AD1\nA(S4)+S3\nA(S5)+S4"
            },
            "Tiaoxin-346": {
                "num_block_types": "3",
                "num_blocks": "3 4 6",
                "block_names": "U V W",
                "num_ad_types": "3",
                "ad_counts": "1 1 1",
                "ad_names": "a b c",
                "round_functions": "U0+a0+A(U2)\nA(U0)\nU1\nV0+b0+A(V3)\nA(V0)\nV1\nV2\nW0+c0+A(W5)\nA(W0)\nW1\nW2\nW3\nW4"
            }
        }
        
        self.cipher_type_combo.currentTextChanged.connect(self.populate_scheme_fields)
        self.analyze_button.clicked.connect(self.analyze)
        self.exit_button.clicked.connect(self.close)

    def populate_scheme_fields(self):
        selected_scheme = self.cipher_type_combo.currentText()
        if selected_scheme in self.scheme_defaults:
            scheme_data = self.scheme_defaults[selected_scheme]
            self.input_text_edit.setText(scheme_data["num_block_types"])
            self.input_text_edit_2.setText(scheme_data["num_blocks"])
            self.input_text_edit_3.setText(scheme_data["block_names"])
            self.input_text_edit_4.setText(scheme_data["num_ad_types"])
            self.input_text_edit_5.setText(scheme_data["ad_counts"])
            self.input_text_edit_6.setText(scheme_data["ad_names"])
            self.input_text_edit_7.setPlainText(scheme_data["round_functions"])

    def analyze(self):
        # Get the cipher type and input text
        cipher_type = self.cipher_type_combo.currentText()

        try:
            num_block_types = int(self.input_text_edit.toPlainText().strip())
            num_blocks = list(map(int, self.input_text_edit_2.toPlainText().strip().split()))
            block_names = self.input_text_edit_3.toPlainText().strip().split()
            num_ad_types = int(self.input_text_edit_4.toPlainText().strip())
            ad_counts = list(map(int, self.input_text_edit_5.toPlainText().strip().split()))
            ad_names = self.input_text_edit_6.toPlainText().strip().split()
            round_functions = self.input_text_edit_7.toPlainText().strip().split('\n')
            inputs = num_block_types, num_blocks, block_names, num_ad_types, ad_counts, ad_names, round_functions
            if inputs is not None:
                if cipher_type == 'Custom':
                    if num_ad_types == 3:
                        response, ok = QInputDialog.getText(self, "Input", f"Do the associated data have the following relationship: {ad_names[0]} + {ad_names[1]} = {ad_names[2]}? (Y/N):")
                        if ok and response.lower() == 'y':
                            cipher_type = 'Tiaoxin-346'
                
                if cipher_type == 'Tiaoxin-346':
                    if num_ad_types != 3:
                        QMessageBox.warning(self, "Error", "Try Custom!")
                        return
                    num_rounds = find_minimum_rounds(block_names, ad_names, num_blocks, ad_counts, round_functions)
                    equations = generate_equations(round_functions, block_names, ad_names, ad_counts, num_blocks, num_rounds)
                    unknowns_before_guessing, guesses = analyze_security_with_guessing(equations, block_names, ad_names, num_blocks, ad_counts, num_rounds)
                    result = f"Attack rounds: {num_rounds}\nUnknown values before guessing: {unknowns_before_guessing}\nGuesses needed to resolve all unknowns: {guesses}"
                elif cipher_type == 'AEGIS-128' or 'AEGIS-128L' or 'AEGIS-256':
                    if num_ad_types not in [1, 2]:
                        QMessageBox.warning(self, "Error", "Try Custom!")
                        return
                    num_rounds = find_minimum_rounds(block_names, ad_names, num_blocks, ad_counts, round_functions)
                    equations = generate_equations(round_functions, block_names, ad_names, ad_counts, num_blocks, num_rounds)
                    security_level = analyze_security(equations, block_names, ad_names, num_blocks, ad_counts, num_rounds)
                    if not isinstance(security_level, int):
                        QMessageBox.warning(self, "Error", "Analysis cannot be performed.")
                        return
                    result = f"Attack rounds: {num_rounds}\nComplexity: 2^{security_level}"
                elif cipher_type == 'Rocca' or 'Rocca-S':
                    if num_ad_types != 2:
                        QMessageBox.warning(self, "Error", "Try Custom!")
                        return
                    num_rounds = find_minimum_rounds(block_names, ad_names, num_blocks, ad_counts, round_functions)
                    equations = generate_equations(round_functions, block_names, ad_names, ad_counts, num_blocks, num_rounds)
                    security_level = analyze_security(equations, block_names, ad_names, num_blocks, ad_counts, num_rounds)
                    if not isinstance(security_level, int):
                        QMessageBox.warning(self, "Error", "Analysis cannot be performed.")
                        return
                    result = f"Attack rounds: {num_rounds}\nComplexity: 2^{security_level}"
                else:
                    num_rounds = find_minimum_rounds(block_names, ad_names, num_blocks, ad_counts, round_functions)
                    equations = generate_equations(round_functions, block_names, ad_names, ad_counts, num_blocks, num_rounds)
                    security_level = analyze_security(equations, block_names, ad_names, num_blocks, ad_counts, num_rounds)
                    if not isinstance(security_level, int):
                        QMessageBox.warning(self, "Error", "Analysis cannot be performed.")
                        return
                    result = f"Attack rounds: {num_rounds}\nComplexity: 2^{security_level}"
                
                # Generate the equations with T_{index} = format
                formatted_equations = []
                for block_type_index, block_name in enumerate(block_names):
                    for block_index in range(num_blocks[block_type_index]):
                        if num_block_types == 1:
                            formatted_equations.append(f"T_{block_index} = {equations[sum(num_blocks[:block_type_index]) + block_index]}")
                        else:
                            formatted_equations.append(f"T_{block_name}_{block_index} = {equations[sum(num_blocks[:block_type_index]) + block_index]}")
                
                # Display equations with a blank line between each equation
                equations_text = '\n\n'.join(formatted_equations)
                self.equation_text_edit.setPlainText(equations_text)

                # Display result
                self.result_text_edit.setPlainText(result)
            else:
                QMessageBox.warning(self, "Error", "Invalid input format.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = KeyCommittingTool()
    window.show()
    sys.exit(app.exec_())
