---
title: "Statistical distributions for fisheries and marine ecology"
date: 2026-07-06
permalink: /blog/statistical-distributions-fisheries-marine-ecology/
categories:
  - statistical-ecology
tags:
  - distributions
  - GLM
  - GAM
  - CPUE
  - zero-inflation
  - marine-ecology
  - fisheries
  - R
series: "Quantitative marine ecology"
post_type: "technical-note"
level: "intermediate"
excerpt: "A practical guide to choosing statistical distributions for presence–absence, counts, CPUE, biomass, proportions, compositional data, and extreme events in fisheries and marine ecology."
header:
  teaser: posts/20260706_statdist_fish/teaser.png
---

{% include toc title="Contents" %}

## Summary

Statistical distributions are not only mathematical objects. In fisheries and marine ecology, they represent assumptions about the data-generating process behind observations such as species presence, abundance, CPUE, acoustic biomass, size composition, juvenile fraction, environmental anomalies, or extreme events.

This technical note provides a practical guide for choosing distributions according to the type of response variable and the ecological or fisheries process being analysed.

> **Key message.**  
> The distribution is a biological and statistical assumption about how the data were generated.

## 1. Why statistical distributions matter in fisheries and marine ecology

Marine ecological and fisheries data are rarely simple. They often include zero inflation, overdispersion, spatial aggregation, temporal autocorrelation, measurement error, and strong environmental forcing. For this reason, selecting an adequate statistical distribution is a central step in model formulation.

For example, presence–absence data require a Bernoulli or Binomial structure, count data may require a Poisson or Negative binomial model, CPUE data often require delta or Tweedie models, and compositional data should be represented using Multinomial or Dirichlet-type models.

## 2. Start with the data-generating process

A useful first question is:

> What process generated the response variable?

The answer determines the candidate distribution.

| Type of response | Fisheries or ecological example | Candidate distributions |
|---|---|---|
| Binary | Presence or absence of anchovy | Bernoulli, Binomial |
| Count | Number of eggs, larvae, individuals, or species | Poisson, Negative binomial |
| Count with many zeros | Rare bycatch species, incidental catch | Zero-inflated, Hurdle |
| Positive continuous | Positive CPUE, biomass, weight | Gamma, Lognormal |
| Zero plus positive continuous | CPUE with many zeros | Delta-Gamma, Delta-lognormal, Tweedie |
| Proportion | Juvenile fraction, maturity proportion | Beta, Binomial |
| Composition | Length composition, diet, species composition | Multinomial, Dirichlet |
| Time-to-event | Survival, degradation, duration | Exponential, Weibull, Gamma |
| Extreme values | Marine heatwaves, El Niño extremes | GEV, Gumbel, Pareto |

## 3. Presence–absence data

Presence–absence data are naturally represented using a Bernoulli distribution:

$$
Y_i \sim Bernoulli(p_i)
$$

where \(Y_i = 1\) indicates presence and \(Y_i = 0\) indicates absence.

In fisheries and marine ecology, this structure is useful for modelling:

- presence of anchovy in an acoustic station;
- catch or no catch in a fishing set;
- occurrence of a bycatch species;
- presence of juveniles in a sample.

A generalized additive model may be written as:

$$
logit(p_i) = \beta_0 + f(SST_i) + f(CHL_i) + f(DC_i)
$$

where \(SST\) is sea surface temperature, \(CHL\) is chlorophyll-a, and \(DC\) is distance to the coast.

## 4. Count data and overdispersion

Count data include the number of eggs, larvae, individuals, schools, species, or events observed in a sampling unit.

A first candidate is the Poisson distribution:

$$
Y_i \sim Poisson(\lambda_i)
$$

However, the Poisson assumes that the mean and variance are approximately equal. This assumption is often unrealistic in marine systems because organisms are spatially aggregated in schools, patches, fronts, or productive areas.

When the variance is larger than the mean, the Negative binomial distribution is usually more appropriate:

$$
Y_i \sim NegativeBinomial(\mu_i, k)
$$

This distribution is particularly useful for overdispersed ecological counts.

## 5. CPUE, zero inflation, and delta models

CPUE data commonly have:

- many zeros;
- positive skewness;
- strong spatial and temporal variability;
- occasional extreme values.

A delta model separates two processes:

1. the probability of encounter;
2. the positive catch rate conditional on encounter.

The occurrence component is:

$$
Pr(Y_i > 0) \sim Bernoulli(p_i)
$$

The positive component may be:

$$
Y_i | Y_i > 0 \sim Gamma(\mu_i, \phi)
$$

This structure is useful because a zero catch may reflect true absence, low availability, low detectability, operational decisions, or environmental mismatch.

## 6. Biomass and positive continuous variables

Positive continuous variables include biomass, acoustic density, individual weight, positive CPUE, chlorophyll concentration, and oxygen concentration when measured on a positive scale.

Useful distributions include:

- Gamma;
- Lognormal;
- Tweedie;
- Delta-lognormal;
- Delta-Gamma.

For acoustic biomass, a Lognormal model may be reasonable when the observed biomass is generated by multiplicative processes such as aggregation, environmental suitability, detectability, and local concentration.

## 7. Proportions and compositional data

Proportions occur frequently in fisheries science:

- fraction of juveniles;
- proportion of mature individuals;
- fraction of area occupied;
- proportion of bycatch;
- proportion of diet items.

If the numerator and denominator are known, a Binomial model is usually preferable:

$$
J_i \sim Binomial(n_i, p_i)
$$

where \(J_i\) is the number of juveniles and \(n_i\) is the total number of measured individuals.

If only a continuous proportion between 0 and 1 is available, a Beta distribution may be used.

Compositional data, such as length composition or diet composition, require models that acknowledge that all categories are jointly constrained and often sum to one. Candidate distributions include the Multinomial and Dirichlet.

## 8. Environmental variables and anomalies

Environmental variables may follow different distributions depending on scale and transformation.

| Variable | Possible distribution |
|---|---|
| Temperature anomaly | Normal, Student-t |
| Chlorophyll-a | Lognormal, Gamma |
| Oxygen concentration | Normal, Gamma, Lognormal |
| Wind direction | Circular distributions |
| Extreme temperature | GEV, Gumbel |

For standardized anomalies, a Normal or Student-t distribution is often used. The Student-t distribution can be useful when the variable has heavier tails than expected under a Normal distribution.

## 9. Extreme events

Extreme value distributions are useful when the interest is not the mean state of the system but rare events with high ecological or fisheries impact.

Examples include:

- extreme El Niño events;
- marine heatwaves;
- minimum oxygen events;
- unusually high recruitment events;
- exceptionally high catches;
- extreme displacement of the fleet.

Candidate distributions include GEV, Gumbel, and Pareto.

## 10. Practical decision table

| Question | Distribution |
|---|---|
| Is the response binary? | Bernoulli |
| Is it the number of successes out of a known total? | Binomial |
| Is it a count with mean close to variance? | Poisson |
| Is it an overdispersed count? | Negative binomial |
| Are there too many zeros? | Zero-inflated or hurdle model |
| Is it positive and continuous? | Gamma or Lognormal |
| Is it zero plus positive continuous? | Delta model or Tweedie |
| Is it a proportion? | Beta or Binomial |
| Is it a composition? | Multinomial or Dirichlet |
| Is it a time-to-event variable? | Exponential, Weibull, or Gamma |
| Is the focus on extremes? | GEV, Gumbel, or Pareto |

## 11. Minimal R examples

```r
library(mgcv)

# Presence–absence
m_presence <- gam(
  presence ~ s(sst) + s(chl) + s(distance_coast),
  family = binomial(link = "logit"),
  data = dat
)

# Overdispersed counts
m_count <- gam(
  count ~ s(sst) + s(chl) + s(latitude),
  family = nb(),
  data = dat
)

# Positive CPUE
m_cpue_positive <- gam(
  cpue ~ s(sst) + s(chl) + s(distance_coast),
  family = Gamma(link = "log"),
  data = subset(dat, cpue > 0)
)

# Proportion data
m_juveniles <- gam(
  juvenile_prop ~ s(sst) + s(month, bs = "cc"),
  family = betar(link = "logit"),
  data = dat
)
```

## 12.Common mistakes
1. Using a Normal distribution for strongly skewed positive data.
2. Using Poisson models when the data are clearly overdispersed.
3. Ignoring excess zeros in CPUE or bycatch data.
4. Treating compositional categories as independent proportions.
5. Choosing a distribution only by visual fit without considering the ecological process.
6. Ignoring the sampling design, effort, or detectability.

## 13. Take-home message
The choice of a statistical distribution should be treated as part of the ecological model, not as a technical detail. In fisheries and marine ecology, each distribution should be linked to the response type, the sampling process, the scale of measurement, and the biological or fisheries mechanism behind the data.

For practical modelling, the first diagnostic step is to classify the response variable: binary, count, positive continuous, zero-inflated, proportional, compositional, time-to-event, or extreme. This classification provides a defensible starting point for GLM, GAM, GLMM, spatio-temporal models, and Bayesian models.

Suggested citations:

Quispe-Salazar, E. (2026). Statistical distributions for fisheries and marine ecology. Technical Blog. https://qselmer.github.io/blog/statistical-distributions-fisheries-marine-ecology/.