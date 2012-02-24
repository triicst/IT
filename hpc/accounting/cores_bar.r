library(ggplot2)

args=(commandArgs(TRUE))

if (length(args)==0) {
   input_file="cluster.csv"
} else {
   input_file=args
}

cores=read.csv(input_file)
cores$Date=as.Date(cores$Date,"%Y-%m-%d")
ggplot(data=cores,aes(x=Date,y=MaxCores,fill=User))+geom_bar(stat="identity")+scale_y_continuous("MaxCores")+scale_x_date()
