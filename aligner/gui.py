import sys
import tkinter
import traceback
import tkinter as tk
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from utils import norm_columns
from utils import timestamp_to_elapsed


def manual_align(true_time_data, scale=None, **data_to_align):
    aligner = AlignGUI(true_time_data, data_to_align)
    aligner.next()

    if scale is not None:
        aligner.rescale(
            scale / aligner.current_scale.get()
        )

    aligner.run()
    alignments = {}
    for name, align in aligner.complete_alignments.items():
        alignments[name] = pd.Timedelta(seconds=align)
    warnings = {}
    if aligner.gen_warning_flag.get():
        warnings['general warning'] = 'Aligner was generally concerned with the quality of the alignment'
    if aligner.align_shift_flag.get():
        warnings['shift warning'] = 'Suspected data shift, alignments do not match across recording'
    if aligner.data_missing_flag.get():
        warnings['data missing warning'] = 'Enough data was missing that this alignment is uncertain'
    alignments['warnings'] = warnings
    return alignments


class AlignGUI(object):

    def __init__(self, true_time_source=None, align_sources=None):

        self.true_time_data = None
        self.data_to_align = None
        self.complete_alignments = {}
        self.align_names = None
        self.align_index = -1

        self.down_sample_range = None

        self.window = None

        self.init_window()

        # Tk Variables that need to be kept track of
        self.status = tk.StringVar(master=self.window, value='Initializing...')
        self.down_sample_current = tk.IntVar(master=self.window, value=10)
        self.t_window_start = tk.DoubleVar(master=self.window, value=0.0)
        self.t_window_end = tk.DoubleVar(master=self.window, value=0.0)
        self.align_offset = tk.DoubleVar(master=self.window, value=0.0)
        self.data_missing_flag = tk.BooleanVar(master=self.window, value=False)
        self.align_shift_flag = tk.BooleanVar(master=self.window, value=False)
        self.gen_warning_flag = tk.BooleanVar(master=self.window, value=False)
        self.currently_aligning = tk.StringVar(master=self.window)
        self.zoom_factor = tk.DoubleVar(master=self.window, value=2.0)
        self.look_factor = tk.DoubleVar(master=self.window, value=4.0)
        self.shift_factor = tk.DoubleVar(master=self.window, value=30.0)
        self.scale_factor = tk.DoubleVar(master=self.window, value=1.1)
        self.current_scale = tk.DoubleVar(master=self.window, value=1)
        self.plot_axis = tk.StringVar(master=self.window, value='norm')

        self.prep_data(true_time_source, align_sources)

        # Tk window elements that need to be kept track of
        self.status_label = None
        self.graphing_frame = None
        self.disposable_graphing = None
        self.control_frame = None
        self.pose_frame_plots = None
        self.timeseries_canvas = None
        self.timeseries_figure = None
        self.ground_truth_ts = None
        self.aligning_ts = None
        self.other_ts = None

        self.init_layout()

        self.begin_alignment()
        self.bind_keys()

    @property
    def window_dims(self):
        return self.window.winfo_height(), self.window.winfo_width()

    def bind_keys(self):
        self.window.bind('z', self.zoom_in)
        self.window.bind('x', self.zoom_out)
        self.window.bind('s', self.shift_warn)
        self.window.bind('d', self.data_warn)
        self.window.bind('f', self.gen_warn)
        self.window.bind('<Up>', self.scale_up)
        self.window.bind('<Down>', self.scale_down)
        self.window.bind('<Left>', self.look_left)
        self.window.bind('<Right>', self.look_right)
        self.window.bind('<Shift-Left>', self.shift_left)
        self.window.bind('<Shift-Right>', self.shift_right)
        self.window.bind('<Control-Shift-Left>', self.fine_shift_left)
        self.window.bind('<Control-Shift-Right>', self.fine_shift_right)

        self.window.bind('<Delete>', self.reset_plot)
        self.window.bind('<Return>', self.next)
        self.window.bind('<BackSpace>', self.prev)

    def init_window(self):
        self.window = tk.Tk()
        try:
            self.window.attributes('-zoomed', True)
        except tkinter.TclError:
            self.window.state('zoomed')
        self.window.title('Manual Time Alignment')
        self.window.geometry("500x500")
        tk.Tk.report_callback_exception = self.show_error

    def init_layout(self):
        self.graphing_frame = tk.Frame(self.window)
        self.graphing_frame.pack(side=tk.LEFT)

        self.control_frame = tk.Frame(self.window)
        self.init_control()
        self.control_frame.pack(side=tk.RIGHT)

    def init_control(self):

        # Add a label showing the current alignment offset
        offset_frame = tk.Frame(master=self.control_frame, pady=20)
        offset_frame.pack(side=tk.TOP)
        tk.Label(master=offset_frame, text='Current Offset: ', font=('Arial', 16)).pack(side=tk.LEFT)
        tk.Label(master=offset_frame, textvariable=self.align_offset, font=('Arial', 16)).pack(side=tk.LEFT)
        tk.Label(master=offset_frame, text=' s', font=('Arial', 16)).pack(side=tk.LEFT)

        flag_frame = tk.Frame(master=self.control_frame, pady=10)
        warning_frame = tk.Frame(master=flag_frame)
        tk.Label(master=warning_frame, text='General Warning Flag: ', font=('Arial', 12)).pack(side=tk.LEFT)
        tk.Checkbutton(master=warning_frame, variable=self.gen_warning_flag).pack(side=tk.RIGHT)
        warning_frame.pack()
        missing_frame = tk.Frame(master=flag_frame)
        tk.Label(master=missing_frame, text='Missing Data Flag: ', font=('Arial', 12)).pack(side=tk.LEFT)
        tk.Checkbutton(master=missing_frame, variable=self.data_missing_flag).pack(side=tk.RIGHT)
        missing_frame.pack()
        shift_frame = tk.Frame(master=flag_frame)
        tk.Label(master=shift_frame, text='Shifting Alignment Flag: ', font=('Arial', 12)).pack(side=tk.LEFT)
        tk.Checkbutton(master=shift_frame, variable=self.align_shift_flag).pack(side=tk.RIGHT)
        shift_frame.pack()

        flag_frame.pack()

        self.status_label = tk.Label(master=self.control_frame, width=100, textvariable=self.status, wraplength=200)
        self.status_label.pack(side=tk.BOTTOM)

        tk.Button(master=self.control_frame, text='Reset Plot', command=self.reset_plot).pack(side=tk.BOTTOM)

    def begin_alignment(self):
        self.currently_aligning.set(self.align_names[0])
        self.plot_all_timeseries()
        self.update_canvas()

    def destroy_plot(self):
        try:
            self.disposable_graphing.destroy()
        except AttributeError:
            pass

    def clear_plotting(self):
        self.destroy_plot()
        self.pose_frame_plots = None
        self.timeseries_canvas = None
        self.timeseries_figure = None
        self.ground_truth_ts = None
        self.aligning_ts = None
        self.other_ts = None

    def close_messasge(self):
        self.destroy_plot()
        self.disposable_graphing = tk.Frame(self.graphing_frame, borderwidth=1, padx=0.25 * self.window_dims[1])
        tk.Label(
            master=self.disposable_graphing,
            font=('Arial', 16),
            justify='left',
            text='Alignment complete.'
        ).pack()
        tk.Label(
            master=self.disposable_graphing,
            font=('Arial', 12),
            justify='left',
            text='Press ENTER to close, or BACKSPACE to go back'
        ).pack()
        self.disposable_graphing.pack()

    def reset_plot(self, *args):
        self.clear_plotting()
        self.set_data_lims()
        self.plot_all_timeseries()
        self.t_window_update()
        self.update_status('Ready!')

    def plot_all_timeseries(self):

        self.status.set('Re-plotting all...')
        self.destroy_plot()
        self.disposable_graphing = tk.Frame(self.graphing_frame, borderwidth=1)
        self.disposable_graphing.pack()

        h, w = self.window_dims
        h = int(round(3 / 8 * h))
        w = int(round(3 / 4 * w))
        fig = plt.Figure(figsize=(w / 100, h / 100))
        ax = fig.add_subplot(1, 1, 1)

        self.plot_true_time_ts(ax)
        # self.plot_other_ts(ax)
        self.plot_aligning_ts(ax)
        fig.axes[0].legend()
        fig.axes[0].set_xlabel('Time Elapsed (s)')
        self.set_data_lims()

        canvas = FigureCanvasTkAgg(fig, master=self.disposable_graphing)
        canvas.draw()
        canvas.get_tk_widget().pack()
        self.timeseries_canvas = canvas
        self.timeseries_figure = fig
        self.t_window_update()
        self.update_status('Ready!')

    def get_data_range(self, data_src):
        selection = np.logical_and(
            self.t_window_start.get() < data_src.index,
            data_src.index <= self.t_window_end.get()
        )
        return data_src[selection]

    def plot_true_time_ts(self, axes):
        self.ground_truth_ts = self.plot_ts(self.true_time_data, axes, 'Watch', 'tab:blue')

    def plot_aligning_ts(self, axes):
        self.aligning_ts = self.plot_ts(
            self.aligning_data * self.scale_factor.get(),
            axes, 'ins', 'tab:orange')

    def plot_ts(self, src_data, axes, label, color):
        data = self.get_data_range(src_data)
        time = np.array(data.index)
        values = data[self.plot_axis.get()]
        return axes.plot(time, values, label=label, alpha=0.5, color=color)[0]

    def update_canvas(self):
        self.timeseries_canvas.draw()
        self.timeseries_canvas.flush_events()

    def zoom_in(self, *args):
        indent = self.t_window_width / (self.zoom_factor.get() * 2)
        self.t_window_update(
            self.t_window_start.get() + indent,
            self.t_window_end.get() - indent
        )

    def next(self, *args):
        if self.align_index is None:
            # Close and exit
            self.window.quit()
            self.window.destroy()
            return

        self.complete_alignments[self.currently_aligning.get()] = self.align_offset.get()
        self.align_index += 1
        try:
            next_name = self.align_names[self.align_index]
        except IndexError:
            self.align_index = None
            self.update_status('Complete')
            print("All alignments complete. Ready to exit")
            self.close_messasge()
        else:
            self.currently_aligning.set(next_name)
            self.aligning_ts = self.data_to_align[next_name]
            self.plot_all_timeseries()
            self.update_canvas()

    def prev(self, *args):
        try:
            self.align_index -= 2
        except TypeError:
            self.align_index = -2
        self.next()

    @property
    def t_window_width(self):
        return self.t_window_end.get() - self.t_window_start.get()

    @property
    def aligning_data(self):
        return self.data_to_align[self.currently_aligning.get()]

    def zoom_out(self, *args):
        new_width = self.t_window_width / (1 - 1 / self.zoom_factor.get())
        un_indent = new_width / (2 * self.zoom_factor.get())
        self.t_window_update(
            self.t_window_start.get() - un_indent,
            self.t_window_end.get() + un_indent
        )

    def look_left(self, *args):

        self.t_window_update(
            self.t_window_start.get() - self.t_window_width / self.look_factor.get(),
            self.t_window_end.get() - self.t_window_width / self.look_factor.get()
        )

    def look_right(self, *args):

        self.t_window_update(
            self.t_window_start.get() + self.t_window_width / self.look_factor.get(),
            self.t_window_end.get() + self.t_window_width / self.look_factor.get()
        )

    def shift_left(self, *args):
        self.update_alignment(-1 * self.t_window_width / self.shift_factor.get())

    def shift_right(self, *args):
        self.update_alignment(self.t_window_width / self.shift_factor.get())

    def scale_up(self, *args):
        self.rescale(self.scale_factor.get())

    def scale_down(self, *args):
        self.rescale(1 / self.scale_factor.get())

    def update_ylims(self, all_ydata):
        mins, maxes = [], []
        for ydata in all_ydata:
            try:
                mins.append(np.nanmin(ydata))
                maxes.append(np.nanmax(ydata))
            except AttributeError:
                pass
        ymax = 1.1 * max(maxes)
        ymin = 1.1 * min(mins) if min(mins) < 0 else 0.9 * min(mins)
        self.timeseries_figure.axes[0].set_ylim([ymin, ymax])

    def rescale(self, multiplier):
        yscaled = self.aligning_ts.get_ydata() * multiplier
        self.aligning_ts.set_ydata(yscaled)
        self.update_ylims([yscaled, self.ground_truth_ts.get_ydata()])
        self.update_canvas()
        self.current_scale.set(self.current_scale.get() * multiplier)

    def fine_shift_amt(self):
        times = self.aligning_ts.get_xdata()
        return np.median(np.diff(times[:100]))

    def fine_shift_left(self, *args):
        self.update_alignment(-self.fine_shift_amt())

    def fine_shift_right(self, *args):
        self.update_alignment(self.fine_shift_amt())

    def update_alignment(self, new_shift):
        new_ts = self.aligning_ts.get_xdata() + new_shift
        self.aligning_ts.set_xdata(new_ts)
        self.align_offset.set(round(self.align_offset.get() + new_shift, 4))
        self.update_canvas()

    def data_warn(self, *args):
        self.data_missing_flag.set(not self.data_missing_flag.get())

    def gen_warn(self, *args):
        self.gen_warning_flag.set(not self.gen_warning_flag.get())

    def shift_warn(self, *args):
        self.align_shift_flag.set(not self.align_shift_flag.get())

    def t_window_update(self, start=None, end=None):
        if start is None:
            start = self.t_window_start.get()
        else:
            self.t_window_start.set(start)

        if end is None:
            end = self.t_window_end.get()
        else:
            self.t_window_end.set(end)

        self.timeseries_figure.axes[0].set_xlim([start, end])
        self.update_canvas()

    def run(self):
        self.update_status('Press ENTER to begin...')
        self.window.mainloop()

    def update_status(self, status, color='black'):
        self.status.set(status)
        self.status_label.config(fg=color)
        self.status_label.update()

    def show_error(self, *args):
        err, note, tb = sys.exc_info()
        self.update_status(f'ERROR:  {err}\n{note}', color='red')
        traceback.print_exception(err, note, tb)

    def set_data_lims(self):
        self.t_window_start.set(min(self.true_time_data.index[0], self.aligning_data.index[0]))
        self.t_window_end.set(max(self.true_time_data.index[-1], self.aligning_data.index[-1]))

    @staticmethod
    def soft_total_seconds(times, start):
        try:
            seconds = timestamp_to_elapsed(times, start=start)
        except AttributeError:
            seconds = times
        return seconds

    def prep_stream(self, source, start_time):
        normed_true = norm_columns(source)
        centered = normed_true - np.nanmedian(normed_true)
        new_time = self.soft_total_seconds(source.index, start_time)
        ready = pd.DataFrame.from_dict(
            {self.plot_axis.get(): centered, 'time': new_time},
        ).set_index('time')
        return ready

    def prep_data(self, true_time_src, other_sources):

        common_start = true_time_src.index[0]
        self.true_time_data = self.prep_stream(true_time_src, common_start)

        self.data_to_align = {}
        self.align_names = []
        self.complete_alignments = {}
        for name, source in other_sources.items():
            other_src = self.prep_stream(source, common_start)
            self.data_to_align[name] = other_src
            self.align_names.append(name)
            self.complete_alignments[name] = 0.0
