# Statistical distributions for fisheries and marine ecology
# Minimal GAM examples
# Author: Elmer O. Quispe-Salazar

library(mgcv)

# Presence–absence model
m_presence <- gam(
  presence ~ s(sst) + s(chl) + s(distance_coast),
  family = binomial(link = "logit"),
  data = dat
)

# Overdispersed count model
m_count <- gam(
  count ~ s(sst) + s(chl) + s(latitude),
  family = nb(),
  data = dat
)

# Positive CPUE model
m_cpue_positive <- gam(
  cpue ~ s(sst) + s(chl) + s(distance_coast),
  family = Gamma(link = "log"),
  data = subset(dat, cpue > 0)
)

# Proportion model
m_juveniles <- gam(
  juvenile_prop ~ s(sst) + s(month, bs = "cc"),
  family = betar(link = "logit"),
  data = dat
)

