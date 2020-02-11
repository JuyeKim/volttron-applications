from os.path import dirname, abspath, join
import pandas as pd
import sqlite3
import math
import matplotlib.pyplot as plt
import json
from datetime import timedelta
from dateutil import parser


class MV:
    def __init__(self, json_config_file):
        # read config file
        self.file_path = config["file_path"]
        self.ts_col = config["ts"]
        self.consumption_col = config["consumption"]
        self.oat_col = config["oat"]
        self.hp1_status_col = config["hp1_status"]
        self.hp2_status_col = config["hp2_status"]
        self.hw1_status_col = config["hw1_status"]
        self.hw2_status_col = config["hw2_status"]
        self.poolpump_status_col = config["poolpump_status"]
        self.roomtemp1_col = config["roomtemp1"]
        self.roomtemp2_col = config["roomtemp2"]
        self.event_flag_col = config["event_flag"]
        self.event_date_str = config["event_date"]
        self.event_date = parser.parse(config["event_date"])
        self.event_start = parser.parse(config["event_date"] + " " + config["start_time"])
        self.event_end = parser.parse(config["event_date"] + " " + config["end_time"])
        
        self.baseline_method = config["baseline_method"]
        self.adjustment = config["adjustment"]

        self.plot1_config = config["plots"]["plot1"]
        self.plot2_config = config["plots"]["plot2"]
        self.plot3_config = config["plots"]["plot3"]

    def get_data(self):
        df = pd.read_csv(self.file_path)
        df[self.ts_col] = pd.to_datetime(df[self.ts_col])
        df = df.resample("60min", on=self.ts_col).mean()

        # Remove all rows with event_flag=1 before event day
        df_baseline = df[(df[self.event_flag_col] == 0)
                         & (df.index < self.event_date)]

        # Limit to last 10 weekdays or 10 days
        offset = 10
        if self.baseline_method == "week_days":
            df_baseline = df_baseline[df_baseline.index.dayofweek < 5]
            offset = 14
        df_baseline = df_baseline[df_baseline.index >= self.event_date - timedelta(days=offset)]

        # Event day
        df_event = df[(df.index.date >= self.event_date.date())
                      & (df.index.date < self.event_date.date() + timedelta(days=1))]

        df_baseline2 = pd.DataFrame(columns=df.columns)
        df_event2 = pd.DataFrame(columns=df.columns)

        # Calculate baseline & event-day average kw for 24 hours
        num_cols = len(df.columns)
        for hr in range(0, 24):
            df_hr1 = df_baseline[df_baseline.index.hour == hr]
            df_hr1 = df_hr1.iloc[:, list(range(0, num_cols))].mean(axis=0)
            df_baseline2 = df_baseline2.append(df_hr1, ignore_index=True)

            df_hr2 = df_event[df_event.index.hour == hr]
            df_hr2 = df_hr2.iloc[:, list(range(0, num_cols))].mean(axis=0)
            df_event2 = df_event2.append(df_hr2, ignore_index=True)

        # Adjustment for event hours
        if self.adjustment:
            for hr in range(self.event_start.hour, self.event_end.hour):
                adj_hrs = [hr-4, hr-3, hr-2]
                adj_hrs = [x+24 if x<0 else x for x in adj_hrs]
                sum_actual = 0
                sum_baseline = 0
                for adj_hr in adj_hrs:
                    sum_baseline += df_baseline2.at[adj_hr, self.consumption_col]
                    sum_actual += df_event2.at[adj_hr, self.consumption_col]
                adj = sum_actual/sum_baseline
                df_event2.at[hr, self.consumption_col] = adj * df_event2.at[hr, self.consumption_col]

        return df_baseline2, df_event2

    def plot1(self, df_baseline, df_event):
        # Plot
        ax = df_baseline.plot(y=[self.consumption_col], label=["Baseline"])
        df_event.plot(ax=ax, y=[self.consumption_col], label=["Event Day"])

        ax.set_xlabel(" ".join([self.plot1_config["x"], self.event_date_str]))
        ax.set_ylabel(self.plot1_config["y"])

        ax.axvline(x=self.event_start.hour, linewidth=2, color='r', ls='dotted')
        ax.axvline(x=self.event_end.hour, linewidth=2, color='r', ls='dotted')

        # Calculate wholeday and event difference
        event_sum_diff = 0
        for hr in range(self.event_start.hour, self.event_end.hour):
            event_sum_diff += df_baseline.at[hr, self.consumption_col] - df_event.at[hr, self.consumption_col]

        wholeday_sum_diff = df_baseline[self.consumption_col].sum() - df_event[self.consumption_col].sum()

        # Plot
        ax.text(1, 40, "wholeday diff: " + str(round(wholeday_sum_diff, 2)),
                bbox={'facecolor': 'green' if wholeday_sum_diff > 0 else 'red', 'alpha': 0.5, 'pad': 5})
        ax.text(1, 35, "event diff: " + str(round(event_sum_diff, 2)),
                bbox={'facecolor': 'green' if event_sum_diff > 0 else 'red', 'alpha': 0.5, 'pad': 5})

        # Save & close
        plt.savefig("plot1.png")
        plt.close()

    def plot2(self, df_baseline, df_event):
        ax = df_baseline.plot(y=[self.roomtemp1_col], label=["Baseline"])
        df_event.plot(ax=ax, y=[self.roomtemp1_col], label=["Event Day"])

        ax.set_xlabel(" ".join([self.plot2_config["x"], self.event_date_str]))
        ax.set_ylabel(self.plot2_config["y"])

        ax.axvline(x=self.event_start.hour, linewidth=2, color='r', ls='dotted')
        ax.axvline(x=self.event_end.hour, linewidth=2, color='r', ls='dotted')

        sum1 = 0
        sum2 = 0
        for hr in range(self.event_start.hour, self.event_end.hour):
            sum1 += df_event.at[hr, self.consumption_col]
            sum2 += df_baseline.at[hr, self.consumption_col]

        avg_diff = (sum1-sum2)/(self.event_end.hour-self.event_start.hour)
        ax.text(3, 73, "diff: " + str(round(avg_diff, 2)), bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 10})

        plt.savefig("plot2.png")
        plt.close()

    def plot3(self, df_baseline, df_event, device_col):
        # Calculate wholeday and event difference
        wholeday_baseline = df_baseline[device_col].sum()
        wholeday_event = df_event[device_col].sum()
        wholeday_diff = wholeday_baseline - wholeday_event

        event_baseline = 0
        event_event = 0
        event_diff = 0
        for hr in range(self.event_start.hour, self.event_end.hour):
            event_baseline += df_baseline.at[hr, device_col]
            event_event += df_event.at[hr, device_col]
        event_diff = event_baseline - event_event

        # Plot
        wholeday_names = ["Baseline", "Event Day", "Day Diff"]
        wholeday_values = [wholeday_baseline, wholeday_event, wholeday_diff]

        event_names = ["Baseline", "Event Day", "Event Diff"]
        event_values = [event_baseline, event_event, event_diff]

        ax = plt.subplot(121)
        ax.bar(wholeday_names, wholeday_values)
        ax.set_xlabel(" ".join([self.plot3_config["x"], self.event_date_str]))
        ax.set_ylabel(self.plot3_config["y"])

        ax = plt.subplot(122)
        ax.bar(event_names, event_values)
        ax.set_xlabel(self.plot3_config["x"])
        ax.set_ylabel(self.plot3_config["y"])

        # Save & exit
        plt.savefig(f"plot3_{device_col}.png")
        plt.close()

    def run(self):
        df_baseline, df_event = self.get_data()

        df_baseline.to_csv("df_baseline.csv")
        df_event.to_csv("df_event.csv")

        self.plot1(df_baseline, df_event)
        self.plot2(df_baseline, df_event)

        # Plot ONLY IF the column has data
        if self.hp1_status_col in df_baseline.columns:
            self.plot3(df_baseline, df_event, self.hp1_status_col)
        if self.hp2_status_col in df_baseline.columns:
            self.plot3(df_baseline, df_event, self.hp2_status_col)
        if self.hw1_status_col in df_baseline.columns:
            self.plot3(df_baseline, df_event, self.hw1_status_col)
        if self.hw2_status_col in df_baseline.columns:
            self.plot3(df_baseline, df_event, self.hw2_status_col)


if __name__ == "__main__":
    # Load config file
    json_config_file = "config.json"
    with open(json_config_file, 'r') as fp:
        config = json.load(fp)

    # Instantiate MV instance
    mv = MV(config)

    # Plot
    mv.run()