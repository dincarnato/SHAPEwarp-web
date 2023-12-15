#!/usr/bin/perl

use strict;
use CGI;
use File::Copy;
use File::Path qw(mkpath);
use JSON;
use POSIX qw(setsid);

use lib "/var/www/html/scripts/lib";

use Core::Mathematics qw(:all);
use Core::Utils;
use Data::Sequence::Utils;

my ($cgi, $jobId, $queryDir, $queryFh, 
    $newUrl, $msDelay, $error, $maxQueryLen,
    $maxTotQueryLen, $swPath, $nSec, %params);
$msDelay = 5000;
$nSec = int($msDelay / 1000);
$maxQueryLen = 300;
$maxTotQueryLen = $maxQueryLen * 10;
$queryDir = "../queries/";
$swPath = "/usr/local/bin/shapewarp-main/target/release/shapewarp";
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
      <title>SHAPEwarp</title>
      <link rel="shortcut icon" href="https://www.incarnatolab.com/favicon.ico" type="image/x-icon">
      <link rel="stylesheet" href="../css/styles.css">
      <link rel="stylesheet" href="../css/loader.css">
      <link href="https://fonts.googleapis.com/css?family=Merriweather:400,400i|Orbitron:900|Raleway:300,400,400i,600,700" rel="stylesheet">
      <script src="https://code.jquery.com/jquery-3.6.4.min.js"></script>
   </head>
   <body>
      <div id="menu-bar" class="menu-bar">
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

    if (exists $params{database}) {
    
        my ($query, $totLen, $nQueries);
        $jobId = randalphanum(16);
        $queryFh = $cgi->upload("fileInput");

        if (defined $queryFh) { while (<$queryFh>) { $query .= $_; } }
        elsif (exists $params{"query"} && defined $params{"query"}) { $query = $params{"query"}; }

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

            if (my $pid = fork()) {

                $jobId .= "-$pid";
                $newUrl = "shapewarp.cgi?jobId=$jobId";
                
                print <<HTML;
                
                <p>Your job has been successfully submitted (Job ID: <strong>$jobId</strong>)</p>
                <p>Submitted queries: <strong>$nQueries</strong>, Total query length: <strong>$totLen</strong></p>
                <p>Please wait, this page will automatically refresh in <strong>$nSec</strong> seconds...</p>
HTML

            }
            else { # Here we will call the SHAPEwarp process in the background

                my ($queryFile, $dbDir, $outDir, $cmd);
                $jobId .= "-$$";
                $queryFile = $queryDir . $jobId . ".query.txt";
                $dbDir = "../databases/" . $params{"database"} . "/reactivity";
                $outDir = "../results/$jobId/";

                open(my $fh, ">", $queryFile);
                print $fh $query . "\n";
                close($fh);

                $cmd = $swPath . " --query $queryFile --database $dbDir.db";
                $cmd .= -e "$dbDir.shuffled.db" ? " --shuffled-db $dbDir.shuffled.db" :
                                                  " --dump-shuffled-db $dbDir.shuffled.db";
                $cmd .= " --output $outDir --overwrite --threads " . optimalThreadN();
                $cmd .= " --report-alignment s --report-reactivity";
                
                $cmd .= " --$_ " . $params{$_} for (qw(inclusion-evalue report-evalue kmer-len kmer-min-complexity min-kmers
                                                       kmer-offset kmer-max-match-every-nt max-kmer-dist null-hsgs 
                                                       align-mismatch-score align-len-tolerance align-gap-ext-penalty 
                                                       align-match-score align-max-drop-off-rate align-gap-open-penalty 
                                                       max-reactivity max-align-overlap));

                if (exists $params{"match-kmer-gc-content"} && $params{"match-kmer-gc-content"} eq "on") {

                    $cmd .= " --match-kmer-gc-content";
                    $cmd .= " --kmer-max-gc-diff " . $params{"kmer-max-gc-diff"} if (lc($params{"kmer-max-gc-diff"}) ne "auto");

                }

                if (exists $params{"match-kmer-seq"} && $params{"match-kmer-seq"} eq "on") {

                    $cmd .= " --match-kmer-seq";
                    $cmd .= " --kmer-max-seq-dist " . $params{"kmer-max-seq-dist"};

                }

                if (exists $params{"align-score-seq"} && $params{"align-score-seq"} eq "on") {

                    $cmd .= " --align-score-seq";
                    $cmd .= " --$_ " . $params{$_} for (qw(align-seq-match-score align-seq-mismatch-score));

                }

                if (exists $params{"eval-align-fold"} && $params{"eval-align-fold"} eq "on") {

                    $cmd .= " --eval-align-fold";
                    $cmd .= " --$_ " . $params{$_} for (qw(shufflings block-size min-bp-support max-bp-span 
                                                           align-fold-pvalue slope intercept));
                    
                    for (qw(in-block-shuffle no-lonely-pairs no-closing-gu ribosum-scoring)) {

                        $cmd .= " --$_" if (exists $params{$_} && $params{$_} eq "on");

                    }

                }

                # Detaches the process
                setsid();
                fork() and exit();

                my ($stdout, $stderr);
                $stdout = "../logs/$jobId.stdout.txt";
                $stderr = "../logs/$jobId.stderr.txt";

                open(STDIN, "<", "/dev/null");
                open(STDOUT, ">", $stdout);
                open(STDERR, ">", $stderr);

                # Runs SHAPEwarp
                system($cmd);

                if (exists $params{"eval-align-fold"} && $params{"eval-align-fold"} eq "on") {

                    mkpath($outDir . "r2dt_input/", { mode => 0755 });
                    mkpath($outDir . "r2dt_out/results/json/svg/", { mode => 0755 });

                    # R2DT has some issue with paths. We need to place everything in the same dir to work
                    copy("colorscheme.json", $outDir . "r2dt_out/results/json/");

                    makeR2dtInputFiles();
                    makeR2dtStructPlots();

                }

                unlink($stdout) if (!-s $stdout);
                unlink($stderr) if (!-s $stderr);

                open(my $wh, ">", $outDir . "done.out");
                print $wh scalar(localtime());
                close($wh);

                exit();

            }

        }

    }
    else {

        $newUrl = "../index.html";
        $msDelay = 0;

    }

}
else {

    if (-e "../results/$jobId/done.out") {

        $newUrl = "results.cgi?jobId=$jobId";
        $msDelay = 0;

    }
    else {

        print <<HTML;
                <p>
                    This page will automatically refresh every <strong>$nSec</strong> seconds.
                    <br/>
                    Please wait, or bookmark it to retrieve your search results later.
                </p>
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
      <script>
HTML

print <<HTML if (!$error);

        \$(document).ready(function(){
            var msDelay = $msDelay;

            setTimeout(function() {
                window.location.href = "$newUrl";
            }, msDelay);
        });
HTML

print <<HTML;
      </script>
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

        if (exists $ids{$query[$i]}) { $errMsg = "Duplicate query ID \"<strong>$query[$i]</strong>\""; }
        elsif (@query < $i + 3) { $errMsg = "Truncated or malformed query"; }
        elsif (!isna($query[$i + 1])) { $errMsg = "Sequence for query \"<strong>$query[$i]</strong>\" contains invalid charaters"; }
        elsif (length($query[$i + 1]) > $maxQueryLen) { $errMsg = "Query \"<strong>$query[$i]</strong>\" exceeds the server limit of $maxQueryLen nt"; }
        else {

            my @reactivity = split /,/, $query[$i + 2];

            if (@reactivity != length($query[$i + 1])) { $errMsg = "Sequence and reactivities for query \"<strong>$query[$i]</strong>\" have different lengths"; }
            elsif (!isnumeric(grep { $_ ne "NaN" } @reactivity, 1)) { $errMsg = "Invalid reactivity values for query \"<strong>$query[$i]</strong>\""; }
            elsif (isnan(@reactivity)) { $errMsg = "Reactivity values for query \"<strong>$query[$i]</strong>\" are all NaN"; }

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

sub optimalThreadN {

    my ($running, $nCores);
    $running = `ps -ax | grep '$swPath' |grep -v 'grep' |wc -l`;
    $running =~ s/\s//g;
    $running //= $running - 1;

    if ($^O eq "darwin") { chomp($nCores = `sysctl -n hw.ncpu`); }
    elsif ($^O eq "linux") { chomp($nCores = `grep -c -P '^processor\\s+:' /proc/cpuinfo`); }

    $nCores ||= 8;

    return(max(1, int($nCores / ($running + 1))));

}

sub makeR2dtInputFiles {

    my ($outDir, $alnDir, $reactDir, $fastaDir, $tsvDir);
    $outDir = "../results/$jobId/";
    $alnDir = $outDir . "alignments/";
    $reactDir = $outDir . "reactivities/";
    $fastaDir = $outDir . "r2dt_input/";
    $tsvDir = $outDir . "r2dt_out/results/json/";

    opendir(my $dh, $alnDir);
    while (my $file = readdir($dh)) {

        next if ($file !~ /\.sto$/);

        my ($baseName, $structure, $json, %seq);
        $baseName = $file;
        $baseName =~ s/\.sto$//;

        open(my $fh, "<", $alnDir . $file) or die $!;
        while(<$fh>) {

            chomp();

            if (/^#=GC SS_cons/ || /^[^#\/]/) {

                my @row = split " ";

                if ($row[1] eq "SS_cons") { $structure = $row[2]; }
                else { 
                    
                    $row[1] =~ tr/-T/xU/;
                    $seq{keys %seq ? "db" : "query"} = $row[1]; 
                    
                }

            }

        }
        close($fh);

        open($fh, "<", $reactDir . $baseName . ".json") or die $!;
        $json = do { local $/; <$fh> }; 
        close($fh);

        $json = decode_json($json);
        $json->{"db"} = $json->{"target"};

        foreach my $seq (qw(query db)) {

            open(my $wh, ">", $fastaDir . $baseName . ".$seq.fasta") or die $!;
            print $wh ">$baseName.$seq\n" . $seq{$seq} . "\n" . $structure . "\n";
            close($wh);

            @{$json->{$seq}} = map { $_ eq "NaN" ? "nan" : ($_ < 0.4 ? 0 : ($_ < 0.7 ? 0.5 : 1)) } @{$json->{$seq}};

            open($wh, ">", $tsvDir . $baseName . ".$seq.tsv") or die $!;

            print $wh join("\t", qw(residue_index residue_name shape_reactivity)) . "\n";

            for my $i (0 .. $#{$json->{$seq}}) {

                print $wh join("\t", $i + 1, substr($seq{$seq}, $i, 1), $json->{$seq}->[$i]) . "\n";

            }

            close($wh);

        }

    }
    closedir($dh);

}

sub makeR2dtStructPlots {

    my ($outDir, $fastaDir, $tsvDir, $r2dtDir);
    $outDir = "../results/$jobId/";
    $fastaDir = $outDir . "r2dt_input/";
    $r2dtDir = $outDir . "r2dt_out/";
    $tsvDir = $r2dtDir . "/results/json/";


    opendir(my $dh, $fastaDir);
    while(my $file = readdir($dh)) {

        next if ($file !~ /\.fasta$/);

        my $baseName = $file;
        $baseName =~ s/\.fasta$//;

        system("singularity exec /etc/r2dt r2dt.py templatefree $fastaDir/$file $r2dtDir");
        system("cd $tsvDir && singularity exec /etc/r2dt python3 /rna/traveler/utils/enrich_json.py --input-json $baseName.colored.json --input-data $baseName.tsv --output $baseName.json");
        system("cd $tsvDir && singularity exec /etc/r2dt python3 /rna/traveler/utils/json2svg.py -p colorscheme.json -i $baseName.json -o svg/$baseName.svg");

    }
    closedir($dh);

}