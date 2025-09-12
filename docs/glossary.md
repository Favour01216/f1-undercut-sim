# 🏎️ F1 Undercut Simulator Glossary

*Clear definitions of Formula 1 terminology used in the undercut simulation model*

---

## 📚 Core F1 Strategy Terms

### Stint
**Definition**: A continuous period of driving on the same set of tires between pit stops.  
**Model Context**: The DegModel analyzes tire performance degradation within each stint to predict future lap times. Drivers typically complete multiple stints during a race with different tire compounds.

### Degradation  
**Definition**: The gradual loss of tire performance over time, resulting in slower lap times as tires wear out.  
**Model Context**: Our DegModel uses quadratic regression to capture how lap times increase with tire age, accounting for the accelerating nature of tire wear as rubber compounds lose grip.

### Pit Loss
**Definition**: The total time penalty incurred when a driver enters the pit lane, stops for new tires, and rejoins the race.  
**Model Context**: The PitModel samples from historical pit stop data to estimate time losses, typically 20-30 seconds including pit lane transit time, stationary time, and rejoining delays.

### Outlap
**Definition**: The first lap driven immediately after exiting the pit lane with fresh tires.  
**Model Context**: The OutlapModel accounts for cold tire performance penalties, as new tires require 1-2 laps to reach optimal operating temperature, resulting in slower initial lap times despite being fresh.

---

## 🎯 Strategic Maneuvers

### Undercut
**Definition**: A pit strategy where a driver pits earlier than a rival to gain fresh tires, hoping to use superior grip to close the gap and overtake before the rival pits.  
**Model Context**: Our simulation calculates the probability that Driver A (executing the undercut) will emerge ahead of Driver B (staying out longer) after both complete their pit stops.

### Overcut
**Definition**: The opposite of an undercut - staying out longer on old tires while rivals pit, then using fresher tires later in the race to maintain or gain positions.  
**Model Context**: While not directly modeled, overcut scenarios can be analyzed by reversing the driver roles in our undercut simulation framework.

---

## 🚨 Race Control Situations

### SC (Safety Car)
**Definition**: A controlled period during the race where all cars must follow a Safety Car at reduced speed due to track incidents or hazardous conditions.  
**Model Context**: Safety Car periods artificially bunch up the field and don't represent normal racing degradation, so our models filter out these laps to maintain accurate tire performance predictions.

### VSC (Virtual Safety Car)  
**Definition**: A race control measure requiring all drivers to maintain significantly reduced speeds in specific track sectors without deploying a physical Safety Car.  
**Model Context**: Like Safety Car periods, VSC laps involve abnormal speeds and driving patterns that don't reflect typical tire degradation, so they are excluded from our statistical models.

---

## 🔧 Technical Model Terms

### Tire Age
**Definition**: The number of laps completed on the current set of tires, starting from 1 on the outlap.  
**Model Context**: The primary input variable for degradation prediction, with tire performance typically declining quadratically with age.

### Compound
**Definition**: Different tire formulations (SOFT, MEDIUM, HARD) designed for varying performance characteristics and durability.  
**Model Context**: Our OutlapModel maintains separate penalty distributions for each compound, as softer tires warm up faster but may have different initial performance characteristics.

### Gap
**Definition**: The time difference between two drivers' positions on track, measured in seconds.  
**Model Context**: The baseline separation that determines whether an undercut strategy can succeed - larger gaps make undercuts more challenging as more time must be gained.

### Monte Carlo Simulation
**Definition**: A computational method using random sampling to model the probability of different outcomes.  
**Model Context**: We run thousands of simulated pit stop scenarios with randomly sampled pit losses and outlap penalties to calculate the statistical probability of undercut success.

---

## 📊 Statistical Concepts

### R-squared (R²)
**Definition**: A statistical measure indicating how well a regression model fits the observed data, ranging from 0 (no fit) to 1 (perfect fit).  
**Model Context**: Our DegModel requires R² > 0.7 to ensure tire degradation curves are statistically reliable before making lap time predictions.

### Normal Distribution  
**Definition**: A bell-shaped probability distribution characterized by a mean (average) and standard deviation (spread).  
**Model Context**: The PitModel assumes pit stop times follow a normal distribution, allowing us to sample realistic pit loss variations for Monte Carlo simulation.

### Confidence Interval
**Definition**: A range of values that likely contains the true parameter with a specified level of certainty (e.g., 95% confidence).  
**Model Context**: Model predictions include uncertainty bounds to indicate the reliability of undercut probability calculations based on available data quality.

---

## 🏁 Race Context

### Grid Position
**Definition**: The starting order for the race, determined by qualifying performance.  
**Model Context**: While not directly used in current models, starting position influences early race gaps and strategy options that affect undercut opportunities.

### DRS (Drag Reduction System)
**Definition**: An adjustable rear wing system that reduces aerodynamic drag to assist overtaking in designated track zones.  
**Model Context**: Currently not modeled, but DRS availability can influence the effectiveness of undercut attempts by affecting overtaking difficulty post-pit stop.

### Track Position
**Definition**: A driver's current position in the running order, which may differ from championship standings.  
**Model Context**: Maintaining track position through strategic timing is often more valuable than having slightly faster tires, influencing optimal undercut timing decisions.

---

*This glossary supports the F1 Undercut Simulator's mission to make advanced pit strategy analysis accessible to both F1 experts and newcomers to the sport.*
