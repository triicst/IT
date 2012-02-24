library(ggplot2)
library(reshape)

# ./bender.py -g user-division-department-HPC.txt -c slurmjobcomp.log >cluster.csv

args=(commandArgs(TRUE))

if (length(args)==0) {
   input_file="cluster.csv"
} else {
   input_file=args
}

# load data from CSV file
hyrax=read.csv(input_file)

# convert from CPU seconds to hours
hyrax$Time=hyrax$Time/3600

# force internal ordering to match visible ordering
hyrax=sort_df(hyrax,"Time")
hyrax=hyrax[hyrax$Time>5000,]
#hyrax=hyrax[hyrax$Time>200,]
#hyrax=transform(hyrax,User=factor(User,levels=User))
hyrax=transform(hyrax,User=factor(User,levels=User),Group=factor(Group,levels=Group))

# try to suppress scientific notation
options(scipen=5)

# simple plot of users
qplot(User,Time,data=hyrax,ylab="CPU hours")+geom_bar()+coord_flip()+opts(title="Hyrax: Usage by User")

# plot users by group
#gg=ggplot(data=hyrax,aes(User,Time,group=Group,fill=Group))+scale_y_log10()
gg=ggplot(data=hyrax,aes(User,Time,group=Group,fill=Group))
gg=gg+geom_bar(stat="identity")+coord_flip()+opts(title="Hyrax: Usage by User/Group")+labs(y="CPU hours") 
gg

# plot users by division
gg=ggplot(data=hyrax,aes(User,Time,group=Division,fill=Division))
gg=gg+geom_bar(stat="identity")+coord_flip()+opts(title="Hyrax: Usage by User/Division")+labs(y="CPU hours") 
gg

# sum by group
gtotal=ddply(hyrax,.(Group),summarise,sum=sum(Time))
gtotal$percent=gtotal$sum/sum(hyrax$Time)*100
names(gtotal)=c('Group','Time','Percent')

# force internal ordering to match visible ordering
gtotal=sort_df(gtotal,"Time")
gtotal=transform(gtotal,Group=factor(Group,levels=Group))

# plot by group
qplot(Group,Time,data=gtotal,ylab="CPU hours")+geom_bar()+coord_flip()+opts(title="Hyrax: Usage by Group")
