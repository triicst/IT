library(ggplot2)
library(reshape)

# Assume input files are zoid-all.csv and zoid-nobiguser.csv
zoidall=read.csv("zoid-all.csv")
zoidnb=read.csv("zoid-nobiguser.csv")

# Convert dates to R date
zoidall$Date=as.Date(zoidall$Date,"%Y-%m-%d")
zoidnb$Date=as.Date(zoidnb$Date,"%Y-%m-%d")

# Eliminate MinCores (and new Mean/STD) column(s)
zoidall$MinCores=NULL
zoidall$MeanCores=NULL
zoidall$STDCores=NULL

zoidnb$MinCores=NULL
zoidnb$MeanCores=NULL
zoidnb$STDCores=NULL

# Change headers
names(zoidall)=c("Date","W/Biguser Lab")
names(zoidnb)=c("Date","WO/Biguser Lab")

# Convert to long form
zalong=melt(zoidall,id="Date")
znblong=melt(zoidnb,id="Date")

# Merge tables
zall=rbind(zalong,znblong)

# Relabel table
names(zall)=c("Date","Users","Cores")

# Generate Graph
#ggplot(data=zall,aes(x=Date,y=Cores,colour=Users))+geom_line()+scale_y_continuous("Cores")+scale_x_date(format="%b")+geom_smooth()
ggplot(data=zall,aes(x=Date,y=Cores,colour=Users))+geom_line()+scale_y_continuous("Cores")+scale_x_date()+geom_smooth()
