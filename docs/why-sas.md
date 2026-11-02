# Why SAS

Home Assistant ships two helpers that smooth sensors: **Filter** and **Statistics**. SAS covers what
they do not.

## Comparison

| Need                    | HA Filter                                      | HA Statistics             | SAS                                              |
| ----------------------- | ---------------------------------------------- | ------------------------- | ------------------------------------------------ |
| Setup in the UI         | Yes, one filter per helper. Chains need YAML   | Yes, one value per helper | Yes, three stages in one entry                   |
| Chain of filters        | YAML only, the final output is the only sensor | No                        | Lowpass → median → EMA, a sensor for every stage |
| Lowpass                 | `time_constant` counts state changes           | No                        | τ in real seconds, from the time between updates |
| EMA                     | No                                             | No                        | Reaches 95 % after a set number of seconds       |
| Spikes                  | Outlier filter                                 | Median over a window      | Median as the middle stage                       |
| Change the input sensor | New helper                                     | New helper                | Reconfigure keeps entity IDs and history         |

## What Makes the Difference

### Time, Not Samples

Many sensors only report when their value changes. The update rate then swings from 1 s to several
minutes.

A filter that counts samples reacts fast when the input is busy and slow when it is quiet. That is
the opposite of what you want. SAS uses the real time between updates, so a setting means the
same thing at any update rate. See [Filter math](filter-math.md).

### Three Stages in the Right Order

1. Lowpass damps fast noise. A spike becomes a small bump.
2. Median removes the bumps.
3. EMA gives a calm trend with a known response time.

With the built-in helpers this takes YAML, or three Statistics helpers that are not chained.

### A Number You Can Plan With

"Reaches 95 % of a step within 120 s" holds for any input. That makes the EMA safe to use in
automations such as battery control in [HSEM](https://github.com/woopstar/hsem). A Filter
`time_constant` of 10 means 10 s on one sensor and 10 min on another.

## When the Built-In Helpers Are Enough

| You need                                   | Use        |
| ------------------------------------------ | ---------- |
| One moving average or one median           | Statistics |
| Range, throttle or outlier filtering       | Filter     |
| Min, max, percentile or standard deviation | Statistics |
| A stable value that follows real changes   | SAS        |
