# Running PowerShell on Linux via Docker

##Create the image 

With the Dockerfile in your current directory:

```docker
docker build -t fredhutch/powershell .
```

##Run a PowerShell container

```docker
docker run -ti --rm -v /home/rmcdermo:/home fredhutch/powershell
```

The above will create a new container from the image you created in the step above and drop you at the PowerShell command prompt. The path '/home/rmcdermo' on the docker host will be mounted in the conatiner at '/home'.

```
Copyright (C) 2016 Microsoft Corporation. All rights reserved.

PS /> 
```

##Start using PowerShell

In the following example I want to find the top ten files in my home directory (mounted at /home in the container) that where accessed less than seven days ago, sorted descending by size.

```powershell
PS /> Get-ChildItem -path /home -Recurse | Where-Object {$_.PSIsContainer -eq $false -and ($_.LastAccessTime -gt (get-date).AddDays(-7))}| Select-Object -Property Name, Length, LastAccessTime| Sort-Object -Property length -Descending| Select-Object -First 10                                                               
```

Here are the results:

```
Name                                               Length LastAccessTime     
----                                               ------ --------------     
SP042915_072615_mouseTMT_Fusion_SCX_10_03.raw   847031108 08/17/2016 23:00:16
maxquant-scicomp-release6-results-combined.zip  704086704 08/17/2016 22:59:48
HeLa_mock_10min_diQC_080816_01.raw              662623222 08/16/2016 23:24:30
HEK293_mock_10min_diQC_080816_01.raw            655553234 08/16/2016 23:23:07
HEK293_insulin_10min_diQC_080816_01.raw         650253758 08/16/2016 23:22:19
HeLa_EGF_5min_diQC_080816_01.raw                643219232 08/16/2016 23:23:39
HeLa_EGF_10min_diQC_080816_01.raw               634456552 08/16/2016 23:23:21
Programming Computer Vision with Python.pdf      72874552 08/17/2016 22:59:34
Professional SharePoint 2013 Administration.pdf  58589066 08/17/2016 22:59:33
Head First JavaScript -ebooksfeed.com.pdf        53643303 08/17/2016 22:59:02
```

Enjoy!
