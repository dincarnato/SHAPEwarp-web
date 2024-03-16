# SHAPEwarp-web

SHAPEwarp-web is a web user interface to the [SHAPEwarp](https://github.com/dincarnato/SHAPEwarp/) algorithm for RNA structure homology search.
<br/></br>

## Requirements
- RNAFramework v2.8.7 or greater ([https://github.com/dincarnato/RNAFramework/](https://github.com/dincarnato/RNAFramework/))
- SHAPEwarp v1.2 or greater ([https://github.com/dincarnato/SHAPEwarp/](https://github.com/dincarnato/SHAPEwarp/))
- R2DT v1.4 ([https://github.com/RNAcentral/R2DT](https://github.com/RNAcentral/R2DT)), installed as a [Singularity](https://sylabs.io/singularity/) image (please refer to the [installation manual](https://docs.r2dt.bio/en/latest/installation.html))
- A webserver (such as [Apache](https://httpd.apache.org/))

The path to the RNA Framework's `lib/` folder must be added to the `PERL5LIB` environment variable of the user running the webserver process (typically `apache` or `www-data`). Alternatively, the path can be manually changed inside the `results.cgi` and `shapewarp.cgi` scripts (located under `scripts/`), by amending the following line:

```perl
# Change to reflect the actual path to RNA Framework's lib/
use lib "/var/www/html/shapewarp/scripts/lib";
```
<br/>
## Configuration
A number of parameters, including the path to the SHAPEwarp executable and to the R2DT Singularity image, can be specified in the `shapewarp.conf` file.

Parameter names are case sensitive. Parameter/value pairs must be separated by the `=` sign (no spaces):

```text
# SHAPEwarp Configuration File
#
# Parameter           Description
# =========           ===========
# swPath              Full path to the SHAPEwarp executable (if not provided, will assume it is in PATH)
# r2dtPath            Full path to the R2DT Singularity image
# msDelay             Refresh frequency (in millisec)
# maxQueryLen         Maximum allowed length of a single query
# maxTotQueryLen      Maximum allowed cumulative length of multiple queries

swPath=/usr/local/bin/shapewarp-main/target/release/shapewarp
r2dtPath=/etc/r2dt
msDelay=5000
maxQueryLen=500
maxTotQueryLen=5000
```

Depending on the webserver used, the `scripts/` folder might need to be configured to be granted CGI execution permissions. On Apache, this can be achieved by configuring a Virtual Host. For example:

```xml
<VirtualHost *:80>

  ...

  <Directory "/var/www/html/shapewarp/scripts/">
      Require all granted
      Options +ExecCGI
      AddHandler cgi-script .cgi
  </Directory>
  
</VirtualHost>
```

Furthermore, the ownership of the folder containing SHAPEwarp-web must be assigned to the user running the webserver. For example:

```bash
chown -R www-data:www-data shapewarp/
chmod -R 755 shapewarp/
```