#!/usr/bin/perl

use strict;
use CGI;

use lib "/Users/danny/repos/RNAFramework/lib";

use Core::Mathematics qw(:all);
use Core::Utils;
use Data::Sequence::Utils;

my ($cgi, $jobId, $queryDir, $queryFh, 
    $newUrl, $msDelay, $error, $maxQueryLen,
    $maxTotQueryLen, %params);
$msDelay = 5000;
$maxQueryLen = 300;
$maxTotQueryLen = $maxQueryLen * 10;
$queryDir = "../queries/";
$cgi = CGI->new();
%params = map { $_ => $cgi->param($_) } $cgi->param();
$jobId = $params{jobId} if (exists $params{jobId});

print $cgi->header("text/html");

print <<HTML;
<!DOCTYPE html>
<html lang="en">
   <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>SHAPEwarp - Submit a job</title>
      <link rel="stylesheet" href="../css/styles.css">
      <link rel="stylesheet" href="../css/loader.css">
      <link href="https://fonts.googleapis.com/css?family=Merriweather:400,400i|Orbitron:900|Raleway:300,400,400i,600,700" rel="stylesheet">
      <script src="https://code.jquery.com/jquery-3.6.4.min.js"></script>
   </head>
   <body>
      <div class="menu-bar">
         <div class="container">
            <nav>
               <ul>
                  <li><a href="../index.html">Submit a job</a></li>
                  <li><a href="https://github.com/dincarnato/SHAPEwarp/">Standalone</a></li>
                  <li><a href="../help.html">Help</a></li>
               </ul>
            </nav>
         </div>
      </div>
      <header>
         <div class="container">
            <h1 class="page-title"><span class="page-title2">SHAPE</span>WARP</h1>
         </div>
      </header>
      <section id="main-content" style="height: 75%;">
         <div class="container-centered">
            <div class="container">
                <div style="text-align: center;">
HTML

if (!defined $jobId) { 
    
    my ($queryFile, $query, $totLen, $nQueries);
    $jobId = randalphanum(16) . "-" . $$;
    $newUrl = "shapewarp.cgi?jobId=$jobId"; 
    $queryFile = $queryDir . $jobId . ".query.txt";
    $queryFh = $cgi->upload("fileInput");

    if (defined $queryFh) { while (<$queryFh>) { $query .= $_; } }
    elsif (exists $params{query} && defined $params{query}) { $query = $params{query}; }

    ($query, $totLen, $nQueries, $error) = validateQuery($query);

    if ($error) {

        print <<HTML;
                    <h1 class="page-title" style="color: black; font-size: 2em;">
                        <span class="page-title2">Error</span><br/>
                        $error
                    </h1>
                    <p><a href="../index.html">Go back to the homepage</a></p>
HTML

    }
    else {

        open(my $fh, ">", $queryFile);
        print $fh $query . "\n";
        close($fh);

    }

}
else {

    # Correct this to send to results (with right condition)
    if (-e "../queries/test.txt") {

        $newUrl = "https://www.incarnatolab.com/";
        $msDelay = 0;

    }
    else {

        print <<HTML;
                Your results are loading...
                <br/>
                <div class="lds-ellipsis"><div></div><div></div><div></div></div>
HTML

    }

}

print <<HTML;
           </div>
        </div>
      </section>
      <footer>
         <div class="container">
            <a href="https://www.incarnatolab.com/">
                <h1 class="page-title" style="font-size: 1.2rem;">INCA<span class="page-title2" style="font-size: 1.8rem;">RNA</span>TO lab</h1>
            </a>
         </div>
      </footer>
HTML

print <<HTML if (!$error);
    <script>
        \$(document).ready(function(){
            var msDelay = $msDelay;

            setTimeout(function() {
                window.location.href = "$newUrl";
            }, msDelay);
        });
    </script>
HTML

print <<HTML;
    </body>
</html>
HTML

sub validateQuery {

    my $query = shift;

    my ($parsedQuery, $errMsg, $totLen, $nQueries,
        @query, %ids);
    $query =~ s/\r//g;
    @query = split /\n/, $query;

    for (my $i = 0; $i < @query; $i++) {

        next unless ($query[$i]);

        if (exists $ids{$query[$i]}) { $errMsg = "Duplicate query ID <strong>$query[$i]</strong>"; }
        elsif (@query < $i + 3) { $errMsg = "Truncated or malformed query"; }
        elsif (!isna($query[$i + 1])) { $errMsg = "Sequence for query <strong>$query[$i]</strong> contains invalid charaters"; }
        elsif (length($query[$i + 1]) > $maxQueryLen) { $errMsg = "Query <strong>$query[$i]</strong> exceeds the server limit of $maxQueryLen nt"; }
        else {

            my @reactivity = split /,/, $query[$i + 2];

            if (@reactivity != length($query[$i + 1])) { $errMsg = "Sequence and reactivities for query <strong>$query[$i]</strong> have different lengths"; }
            elsif (!isnumeric(grep { $_ ne "NaN" } @reactivity, 1)) { $errMsg = "Invalid reactivity values for query <strong>$query[$i]</strong>"; }
            elsif (isnan(@reactivity)) { $errMsg = "Reactivity values for query <strong>$query[$i]</strong> are all NaN"; }

            if (!$errMsg) {

                $totLen += @reactivity;
                $nQueries++;
                $parsedQuery .= join("\n", @query[$i .. $i + 2]) . "\n";
                $ids{$query[$i]} = 1;

            }

        }

        $errMsg = "Queries exceed the server limit of $maxTotQueryLen nt" if ($totLen > $maxTotQueryLen);

        last if ($errMsg);

        $i += 2;

    }

    return($parsedQuery, $totLen, $nQueries, $errMsg);

}