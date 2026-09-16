"""GUI to pick the audio input/output device and channels.

Saves the selection to config/device.yaml, used by akmeasure.measure.
"""

import tkinter as tk
from tkinter import messagebox, ttk

import sounddevice as sd

from akmeasure.config import load, save


def refresh_channels(listbox, device_name, kind, selected):
    listbox.delete(0, "end")
    n_channels = sd.query_devices(device_name)[f"max_{kind}_channels"]
    for ch in range(1, n_channels + 1):
        listbox.insert("end", ch)
        if ch in selected:
            listbox.selection_set(ch - 1)


def main():
    devices = sd.query_devices()
    out_devices = [d["name"] for d in devices if d["max_output_channels"] > 0]
    in_devices = [d["name"] for d in devices if d["max_input_channels"] > 0]

    cfg = load("device")

    root = tk.Tk()
    root.title("AKmeasure I/O setup")

    tk.Label(root, text="Output device").grid(row=0, column=0, sticky="w")
    out_device = tk.StringVar(value=cfg.get("output_device", out_devices[0]))
    out_combo = ttk.Combobox(root, textvariable=out_device, values=out_devices, width=50, state="readonly")
    out_combo.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(root, text="Output channels").grid(row=1, column=0, sticky="nw")
    out_channels = tk.Listbox(root, selectmode="multiple", exportselection=False, height=8)
    out_channels.grid(row=1, column=1, sticky="w", padx=5)

    tk.Label(root, text="Input device").grid(row=2, column=0, sticky="w")
    in_device = tk.StringVar(value=cfg.get("input_device", in_devices[0]))
    in_combo = ttk.Combobox(root, textvariable=in_device, values=in_devices, width=50, state="readonly")
    in_combo.grid(row=2, column=1, padx=5, pady=5)

    tk.Label(root, text="Input channels").grid(row=3, column=0, sticky="nw")
    in_channels = tk.Listbox(root, selectmode="multiple", exportselection=False, height=8)
    in_channels.grid(row=3, column=1, sticky="w", padx=5)

    out_device.trace_add("write", lambda *_: refresh_channels(
        out_channels, out_device.get(), "output", cfg.get("output_channels", [1])))
    in_device.trace_add("write", lambda *_: refresh_channels(
        in_channels, in_device.get(), "input", cfg.get("input_channels", [1])))
    refresh_channels(out_channels, out_device.get(), "output", cfg.get("output_channels", [1]))
    refresh_channels(in_channels, in_device.get(), "input", cfg.get("input_channels", [1]))

    def on_save():
        selected_out = [out_channels.get(i) for i in out_channels.curselection()]
        selected_in = [in_channels.get(i) for i in in_channels.curselection()]
        if not selected_out or not selected_in:
            messagebox.showerror("AKmeasure", "Select at least one output and one input channel")
            return
        save("device", {
            "output_device": out_device.get(),
            "input_device": in_device.get(),
            "output_channels": selected_out,
            "input_channels": selected_in,
        })
        messagebox.showinfo("AKmeasure", "Saved to config/device.yaml")

    tk.Button(root, text="Save", command=on_save).grid(row=4, column=0, columnspan=2, pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
