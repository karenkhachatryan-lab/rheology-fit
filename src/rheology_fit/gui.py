"""CustomTkinter desktop GUI for rheology-fit.

Requires the 'gui' extra (`pip install rheology-fit[gui]`). This module is
imported lazily by the CLI's `gui` command so that customtkinter is not a
hard dependency of the core package.
"""

from __future__ import annotations

import json
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from rheology_fit import __version__
from rheology_fit.citation import CITATION_APA, CITATION_BIBTEX
from rheology_fit.data import FlowCurveData, load_flow_curve_csv
from rheology_fit.models import classify_flow_behavior, fit_all, select_best_model
from rheology_fit.report import build_figure, export_json, save_report

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

MODEL_NAMES = ("PowerLaw", "HerschelBulkley", "Casson")
PROJECT_EXTENSION = ".rheofitproj"
REPO_URL = "https://github.com/karenkhachatryan-lab/rheology-fit"


class RheologyFitApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"rheology-fit v{__version__}")
        self.geometry("1050x780")
        self.minsize(800, 600)

        self.data = None
        self.csv_path = None
        self.results = None
        self.best = None
        self.canvas = None

        self._build_menu()
        self._build_layout()

    # ------------------------------------------------------------------ menu

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        self.configure(menu=menubar)

        self.file_menu = tk.Menu(menubar, tearoff=False)
        self.file_menu.add_command(label="Open CSV...", command=self.open_csv, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Open Project...", command=self.open_project_dialog)
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Save Project...", command=self.save_project_dialog, state="disabled", accelerator="Ctrl+S"
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Save Report (PDF+PNG)...", command=self.save_report_dialog, state="disabled"
        )
        self.file_menu.add_command(label="Save JSON...", command=self.save_json_dialog, state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.destroy, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=self.file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Refit models", command=self.run_fit)
        edit_menu.add_command(label="Clear", command=self.clear_all)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Documentation (GitHub)", command=lambda: webbrowser.open(REPO_URL))
        help_menu.add_command(label="Cite...", command=self.show_citation)
        help_menu.add_separator()
        help_menu.add_command(label="About rheology-fit", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.bind_all("<Control-o>", lambda e: self.open_csv())
        self.bind_all("<Control-s>", lambda e: self.save_project_dialog())
        self.bind_all("<Control-q>", lambda e: self.destroy())

    def _set_file_menu_state(self, label: str, state: str) -> None:
        self.file_menu.entryconfigure(self.file_menu.index(label), state=state)

    # ---------------------------------------------------------------- layout

    def _build_layout(self) -> None:
        controls = ctk.CTkFrame(self)
        controls.pack(fill="x", padx=10, pady=(10, 5))

        self.path_label = ctk.CTkLabel(controls, text="No file selected", anchor="w")
        self.path_label.pack(side="left", padx=(5, 10), fill="x", expand=True)

        ctk.CTkButton(controls, text="Open CSV...", command=self.open_csv).pack(side="left", padx=5)
        self.fit_button = ctk.CTkButton(
            controls, text="Fit models", command=self.run_fit, state="disabled"
        )
        self.fit_button.pack(side="left", padx=5)

        model_frame = ctk.CTkFrame(self)
        model_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(model_frame, text="Models:").pack(side="left", padx=(5, 10))
        self.model_vars: dict[str, ctk.BooleanVar] = {}
        for name in MODEL_NAMES:
            var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(model_frame, text=name, variable=var).pack(side="left", padx=10)
            self.model_vars[name] = var

        body = ctk.CTkFrame(self)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        self.plot_frame = ctk.CTkFrame(body)
        self.plot_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.metrics_box = ctk.CTkTextbox(body, width=340, font=("Courier New", 12))
        self.metrics_box.pack(side="right", fill="y")

        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=10, pady=(5, 10))

        self.save_report_button = ctk.CTkButton(
            bottom, text="Save report (PDF+PNG)", command=self.save_report_dialog, state="disabled"
        )
        self.save_report_button.pack(side="left", padx=5)
        self.save_json_button = ctk.CTkButton(
            bottom, text="Save JSON", command=self.save_json_dialog, state="disabled"
        )
        self.save_json_button.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(bottom, text="", anchor="w")
        self.status_label.pack(side="left", padx=15, fill="x", expand=True)

    # ------------------------------------------------------------------ data

    def _load_data(self, data: FlowCurveData, display_name: str, selected_models: tuple[str, ...] | None = None) -> None:
        self.data = data
        self.results = self.best = None
        self.path_label.configure(text=f"{display_name}  ({len(self.data)} points)")
        if selected_models is not None:
            for name in MODEL_NAMES:
                self.model_vars[name].set(name in selected_models)
        self.fit_button.configure(state="normal")
        self._set_file_menu_state("Save Project...", "normal")
        self._set_file_menu_state("Save Report (PDF+PNG)...", "disabled")
        self._set_file_menu_state("Save JSON...", "disabled")
        self.save_report_button.configure(state="disabled")
        self.save_json_button.configure(state="disabled")
        self.status_label.configure(text="")
        self._clear_plot()
        self.metrics_box.delete("1.0", "end")

    def open_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            data = load_flow_curve_csv(path)
        except Exception as exc:
            messagebox.showerror("Error loading CSV", str(exc))
            return
        self.csv_path = Path(path)
        self._load_data(data, self.csv_path.name)

    def clear_all(self) -> None:
        self.data = self.csv_path = None
        self.results = self.best = None
        self.path_label.configure(text="No file selected")
        self.fit_button.configure(state="disabled")
        for var in self.model_vars.values():
            var.set(True)
        self._set_file_menu_state("Save Project...", "disabled")
        self._set_file_menu_state("Save Report (PDF+PNG)...", "disabled")
        self._set_file_menu_state("Save JSON...", "disabled")
        self.save_report_button.configure(state="disabled")
        self.save_json_button.configure(state="disabled")
        self.status_label.configure(text="")
        self._clear_plot()
        self.metrics_box.delete("1.0", "end")

    def run_fit(self) -> None:
        if self.data is None:
            return
        selected = tuple(name for name in MODEL_NAMES if self.model_vars[name].get())
        if not selected:
            messagebox.showwarning("No models selected", "Select at least one model to fit.")
            return
        try:
            self.results = fit_all(self.data, selected)
        except Exception as exc:
            messagebox.showerror("Fit failed", str(exc))
            return

        self.best = select_best_model(self.results)
        self._render_plot()
        self._render_metrics()
        self.save_report_button.configure(state="normal")
        self.save_json_button.configure(state="normal")
        self._set_file_menu_state("Save Report (PDF+PNG)...", "normal")
        self._set_file_menu_state("Save JSON...", "normal")
        self.status_label.configure(
            text=f"Best model (AIC): {self.best.model_name}   |   {classify_flow_behavior(self.best)}"
        )

    def _clear_plot(self) -> None:
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

    def _render_plot(self) -> None:
        self._clear_plot()
        fig = build_figure(self.data, self.results, self.best)
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _render_metrics(self) -> None:
        self.metrics_box.delete("1.0", "end")
        lines = [f"Data points: {len(self.data)}", ""]
        for r in self.results:
            marker = "  <- best (AIC)" if r.model_name == self.best.model_name else ""
            lines.append(f"{r.model_name}{marker}")
            lines.append(f"  R2   = {r.r2:.4f}")
            lines.append(f"  RMSE = {r.rmse:.4f}")
            lines.append(f"  AIC  = {r.aic:.2f}")
            for pname, pval in r.params.items():
                perr = r.param_errors.get(pname, float("nan"))
                lines.append(f"  {pname:>4s} = {pval:10.4f} +/- {perr:.4f}")
            lines.append("")
        lines.append(f"Flow behavior ({self.best.model_name}):")
        lines.append(f"  {classify_flow_behavior(self.best)}")
        self.metrics_box.insert("1.0", "\n".join(lines))

    # --------------------------------------------------------------- saving

    def save_report_dialog(self) -> None:
        if self.best is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf"), ("PNG", "*.png")]
        )
        if not path:
            return
        stem = Path(path).with_suffix("")
        saved = save_report(self.data, self.results, self.best, stem, formats=("pdf", "png"))
        messagebox.showinfo("Report saved", "Saved:\n" + "\n".join(str(p) for p in saved))

    def save_json_dialog(self) -> None:
        if self.best is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        stem = Path(path).with_suffix("")
        out = export_json(self.data, self.results, self.best, stem)
        messagebox.showinfo("JSON saved", f"Saved: {out}")

    # ------------------------------------------------------------- projects

    def _project_payload(self) -> dict:
        return {
            "rheology_fit_project_version": 1,
            "app_version": __version__,
            "source_file": str(self.csv_path) if self.csv_path else None,
            "data": {
                "shear_rate": self.data.shear_rate.tolist(),
                "shear_stress": self.data.shear_stress.tolist(),
                "shear_stress_std": self.data.shear_stress_std.tolist() if self.data.shear_stress_std is not None else None,
            },
            "selected_models": [name for name in MODEL_NAMES if self.model_vars[name].get()],
        }

    def save_project_to(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self._project_payload(), indent=2), encoding="utf-8")

    def save_project_dialog(self) -> None:
        if self.data is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=PROJECT_EXTENSION,
            filetypes=[("rheology-fit project", f"*{PROJECT_EXTENSION}")],
        )
        if not path:
            return
        self.save_project_to(path)
        messagebox.showinfo("Project saved", f"Saved: {path}")

    def load_project_from(self, path: str | Path) -> None:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        d = payload["data"]
        data = FlowCurveData(
            shear_rate=np.array(d["shear_rate"], dtype=float),
            shear_stress=np.array(d["shear_stress"], dtype=float),
            shear_stress_std=np.array(d["shear_stress_std"], dtype=float) if d.get("shear_stress_std") else None,
            source=Path(payload.get("source_file") or path),
        )
        self.csv_path = Path(payload.get("source_file") or path)
        selected = tuple(payload.get("selected_models", MODEL_NAMES)) or MODEL_NAMES
        self._load_data(data, f"{Path(path).name} [project]", selected_models=selected)

    def open_project_dialog(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("rheology-fit project", f"*{PROJECT_EXTENSION}"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            self.load_project_from(path)
        except Exception as exc:
            messagebox.showerror("Error loading project", str(exc))
            return
        self.status_label.configure(text="Project loaded — click Fit models to compute results.")

    # ------------------------------------------------------------- dialogs

    def show_citation(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Cite rheology-fit")
        win.geometry("620x380")
        box = ctk.CTkTextbox(win, font=("Courier New", 12))
        box.pack(fill="both", expand=True, padx=10, pady=10)
        box.insert("1.0", CITATION_APA + "\n\n" + CITATION_BIBTEX)
        box.configure(state="disabled")

    def show_about(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("About rheology-fit")
        win.geometry("480x380")
        win.resizable(False, False)

        ctk.CTkLabel(win, text="rheology-fit", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(24, 0))
        ctk.CTkLabel(win, text=f"version {__version__}").pack(pady=(0, 12))
        ctk.CTkLabel(
            win,
            text="Fitting non-Newtonian flow curve models\nto shear stress/rate data for food rheology.",
            justify="center",
        ).pack(pady=(0, 12))
        ctk.CTkLabel(
            win,
            text=(
                "Karen Khachatryan\n"
                "Laboratory of Nanotechnology and Nanomaterials\n"
                "Faculty of Food Technology\n"
                "University of Agriculture in Krakow\n"
                "ORCID: 0000-0001-7823-5406"
            ),
            justify="center",
        ).pack(pady=(0, 12))
        ctk.CTkLabel(win, text="License: MIT").pack()
        link = ctk.CTkLabel(win, text=REPO_URL, text_color=("blue", "#4aa3ff"), cursor="hand2")
        link.pack(pady=(8, 16))
        link.bind("<Button-1>", lambda e: webbrowser.open(REPO_URL))
        ctk.CTkButton(win, text="Close", command=win.destroy).pack(pady=(0, 16))


def main() -> None:
    app = RheologyFitApp()
    app.mainloop()


if __name__ == "__main__":
    main()
