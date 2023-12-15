#!/usr/bin/env perl

use strict;
use CGI;
use JSON;

use lib "/var/www/html/scripts/lib";

use Core::Mathematics qw(:all);

my ($cgi, $jobId, $newUrl, $maxAlnRowLen,
    $maxSVGsize, $plotData);
$cgi = CGI->new();
$jobId = $cgi->param("jobId");
$maxAlnRowLen = 60;
$maxSVGsize = 500;

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
      <link href="https://fonts.googleapis.com/css?family=Merriweather:400,400i|Orbitron:900|Raleway:300,400,400i,600,700" rel="stylesheet">
      <script src="https://code.jquery.com/jquery-3.6.4.min.js"></script>
      <script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
      <script src="https://www.incarnatolab.com/js/svg-pan-zoom.js"></script>
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
HTML

if (!defined $jobId) { 
    
    $newUrl = "../index.html"; 
    print <<HTML;
      <section id="main-content" style="height: 75%;">
         <div class="container-centered">
HTML

}
else {

    if ($jobId !~ m/^[a-z0-9]+-\d+$/i || !-e "../results/$jobId") { # Job not found

        my @errMsg = $jobId !~ m/^[a-z0-9]+-\d+$/i ? ("Invalid Job ID", "The provided job ID is malformed. Fix it and try again") : 
                                                     ("Job Not Found", "The job you were looking for cannot be found");

        print <<HTML;
      <section id="main-content" style="height: 75%;">
         <div class="container-centered">
            <div class="container">
                <div style="text-align: center;">
                    <h1 class="page-title" style="color: black;">
                        <span class="page-title2">Error</span><br/>
                        $errMsg[0]
                    </h1>
                    <p>$errMsg[1]</p>
                    <a href="../index.html">Go back to the homepage</a>
                </div>
            </div>
HTML

    }
    else { # Job exists

        my ($pid);
        ($pid) = $jobId =~ m/^[a-z0-9]+-(\d+)$/i;

        if (-e "../results/$jobId/done.out") {

            if (!getLineCount("../results/$jobId/results.out")) {

                print <<HTML;
        <section id="main-content" style="height: 75%;">
            <div class="container-centered">
                <div class="container">
                    <div style="text-align: center;">
                        <h1 class="page-title"><span class="page-title2">No significant matches</span></h1>
                        <p>No significant matches for query. Please adjust the search parameters and try again.</p>
                        <a href="../index.html">Go back to the homepage</a>
                    </div>
                </div>
HTML

            }
            else {

                my $date = completionDate();

                print <<HTML;
        <section id="main-content">
            <div class="container">
                <section id="results">
                    <p style="text-align: center; margin-bottom: 50px; line-height: 25px;">Results for Job ID: <strong>$jobId</strong><br/>[Completed on $date]</p>
                    <div id="result-container" class="result-container">
HTML

                resultsToTable();

            }

        }
        else {

            if (kill(0, $pid)) { $newUrl = "shapewarp.cgi?jobId=$jobId"; } # Job is still running
            else { # Job is corrupted

                print <<HTML;
      <section id="main-content" style="height: 75%;">
         <div class="container-centered">
            <div class="container">
                <div style="text-align: center;">
                    <h1 class="page-title" style="color: black;">
                        <span class="page-title2">Error</span><br/>
                        Unable to parse SHAPEwarp output
                    </h1>
                    <p>We apologize for the inconvenience. If the problem persists, please contact the <a href="mailto:dincarnato[at]incarnatolab.com">admin</a>.</p>
                    <a href="../index.html">Go back to the homepage</a>
                </div>
            </div>
HTML

            }

        }

    }

}

print <<HTML;
        </div>
      </section>
      <footer>
         <div class="container">
            <h1 class="page-title" style="font-size: 1.2rem;">INCA<span class="page-title2" style="font-size: 1.8rem;">RNA</span>TO lab</h1>
         </div>
      </footer>
      <script>
HTML

if (defined $plotData) {

    print <<HTML;

        var lastClickedTabId = null;
        var lastClickedRowId = null;

		var plotData = {
$plotData
        }

        \$(document).ready(function() {

            \$(".tab").click(function() {
                var tabId = \$(this).attr("id");
                \$(".tab").removeClass("active");
                \$(".tab-content").removeClass("active");
                \$("#" + tabId + "-content").addClass("active");
                \$("#" + tabId).addClass("active");
        
                if (tabId.endsWith("plot")) {
        
                    var layout = {
                        paper_bgcolor: '#ecf0f1',
                        plot_bgcolor: '#ecf0f1',
                        width: \$("#" + tabId + "-content").width(),
                        margin: {
                            t: 75,
                            b: 75
                        },
                        xaxis: {
                            tickangle: -45
                        },
                        xaxis2: {
                            tickangle: -45
                        },
                        yaxis: {
                            range: [0, 1],
                            domain: [0.7, 1],
                            title: {
                                text: "Reactivity"
                            }
                        },
                        yaxis2: {
                            range: [0, 1],
                            domain: [0, 0.3],
                            title: {
                                text: "Reactivity"
                            }
                        },
                        grid: {
                            rows: 2,
                            columns: 1,
                            pattern: 'independent',
                            roworder: 'top to bottom'
                        },
                        showlegend: false,
                        annotations: [{
                            text: 'Query',
                            showarrow: false,
                            xref: 'paper',
                            yref: 'paper',
                            x: 0,
                            y: 1.2,
                            font: {
                                size: 14,
                                color: 'black'
                            }
                        }, {
                            text: 'DB Entry',
                            showarrow: false,
                            xref: 'paper',
                            yref: 'paper',
                            x: 0,
                            y: 0.48,
                            font: {
                                size: 14,
                                color: 'black'
                            }
                        }]    
                    };

                    var menuBar = {
                        modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'],
                        modeBarButtonsToAdd: [{
                            name: 'Save image as SVG',
                            icon: Plotly.Icons.camera,
                            click: function(gd) {
                                Plotly.downloadImage(gd, {format: 'svg'})
                            }
                        }]
                    };
        
                    Plotly.newPlot(\$("#" + tabId + "ly")[0], [plotData[tabId + "-query"], plotData[tabId + "-db"]], layout, menuBar);

                }
                else if (tabId.endsWith("structure")) {

                    loadReactPlot("#" + tabId + "-query");
                    loadReactPlot("#" + tabId + "-db");

                }
                
                //\$("#main-content").height(\$("#main-content").height() + \$("#" + tabId + "-content").height() - \$("#" + lastClickedTabId + "-content").height());
        
                lastClickedTabId = tabId;

            });
        });
        
        \$(window).on('load', function() {
            
            //\$("#main-content").height(\$("#main-content").height() + 600);
            \$('.result-row').click(function() {
                var rowId = \$(this).attr('id');
                var detailsDivId = '#' + rowId + '-details';
                var summaryTabId = '#' + rowId + '-summary';
                var containerDivId = '#result-container';
                
                if(lastClickedRowId !== null && lastClickedRowId !== rowId) {
                    var lastClickedDetailsDivId = '#' + lastClickedRowId + '-details';
                    \$(lastClickedDetailsDivId).slideUp();
                }
                
                \$(containerDivId).height('auto');
                
                \$(detailsDivId).slideToggle(function() {
                    var footerHeight = \$('footer').outerHeight();
                    var containerHeight = \$(containerDivId).height();
                    \$(containerDivId).height(containerHeight + footerHeight);
                });
                \$('#' + lastClickedTabId).removeClass("active");
                \$('#' + lastClickedTabId + '-content').removeClass("active");
                \$(summaryTabId).addClass("active");
                \$(summaryTabId + '-content').addClass("active");
                
                lastClickedRowId = rowId;
            });
        });

        function loadReactPlot(svgId) {
            window.panZoomRscape = svgPanZoom(svgId, {
                zoomEnabled: true,
                controlIconsEnabled: true,
                fit: true,
                center: true
            });
        };

        \$(document).ready(function(){
            
            var footer = \$('footer');

            footer.mouseleave(function () {
                footer.show();
            });

            footer.mouseenter(function () {
                footer.hide();
            });
        });
HTML

}

if (defined $newUrl) {

    print <<HTML;
        \$(document).ready(function(){
            setTimeout(function() {
                window.location.href = "$newUrl";
            }, 0);
        });
HTML

}

print <<HTML;
    </script>
    </body>
</html>
HTML

sub resultsToTable {

    my ($header, $n, $hasStruct);
    ($header, $n) = (0, 0);
    $hasStruct = hasStruct();

    open(my $fh, "<", "../results/$jobId/results.out");
    while(<$fh>) {

        chomp;

        if (!$header) {

            $header = 1;

            print <<HTML;
                    <div class="result-row header-row">
                        <div class="result-col">Query</div>
                        <div class="result-col">DB Entry ID</div>
                        <div class="result-col">DB Entry Accession</div>
                        <div class="result-col">Score</div>
                        <div class="result-col">P-value</div>
                        <div class="result-col">E-value</div>
                        <div class="result-col">Significance</div>
                    </div>
HTML

        }
        else {

            my ($type, $id, $accession, $baseName,
                $aln, $qSeq, $dSeq, @row);
            $n++;
            @row = split /\t/;
            $baseName = join("_", $row[1], join("-", @row[4,5]), $row[0], join("-", @row[2,3]));
            $_ = formatValue($_) for (@row[8..10]);
            ($accession, $id) = split /_/, $row[1];
            $accession = accessionToLink($accession);
            $type = $row[-1] eq "?" ? "non-signif" : ($n % 2 ? "odd" : "even");

            print <<HTML;
                    <div class="result-row $type" id="result$n">
HTML

            foreach my $field ($row[0], $id, $accession, @row[8..10], $row[-1]) {

                print <<HTML;
                        <div class="result-col">$field</div>
HTML

            }

            print <<HTML;
                    </div>
                    <div class="details-div $type" id="result$n-details">
                        <div class="tabs">
							<div class="tab" id="result$n-summary">Details</div>
HTML
            if ($row[-1] ne "?") {

                print <<HTML;
							<div class="tab" id="result$n-alignment">Alignment</div>
							<div class="tab" id="result$n-plot">Reactivity plot</div>
HTML

                if ($hasStruct) {

                    print <<HTML;
							<div class="tab" id="result$n-structure">Structure</div>
HTML

                }

                print <<HTML;
                            <div class="tab" id="result$n-downloads">Downloads</div>
HTML

            }

            print <<HTML;
                        </div>
						<div class="tab-content" id="result$n-summary-content">
							<table>
                                <tr>
                                    <td class="detail-col-1">Query ID</td>
                                    <td>$row[0]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">Database Entry ID</td>
                                    <td>$id</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">Database Entry Accession</td>
                                    <td>$accession</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">Query<sub>Start</sub></td>
                                    <td>$row[2]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">Query<sub>End</sub></td>
                                    <td>$row[3]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">DB Entry<sub>Start</sub></td>
                                    <td>$row[4]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">DB Entry<sub>End</sub></td>
                                    <td>$row[5]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">Query<sub>Seed</sub></td>
                                    <td>$row[6]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">DB Entry<sub>Seed</sub></td>
                                    <td>$row[7]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">P-value</td>
                                    <td>$row[9]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">E-value</td>
                                    <td>$row[10]</td>
                                </tr>
HTML

            if ($hasStruct) {

                $_ = formatValue($_) for (@row[11..13]);

                print <<HTML;
                                <tr>
                                    <td class="detail-col-1">Query<sub>Base-pair support</sub></td>
                                    <td>$row[12]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">DB Entry<sub>Base-pair support</sub></td>
                                    <td>$row[11]</td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">MFE P-value</td>
                                    <td>$row[13]</td>
                                </tr>
HTML

            }

            print <<HTML;
                            </table>
						</div>
HTML

            if ($row[-1] ne "?") {

                ($aln, $qSeq, $dSeq) = importStockholm($baseName);
                $plotData .= importJson($baseName, $qSeq, $dSeq, $n);

                print <<HTML;
						<div class="tab-content" id="result$n-alignment-content">
							<pre>$aln</pre>
						</div>
						<div class="tab-content" id="result$n-plot-content">
							<div id="result$n-plotly" style="width:100%; height:400px;"></div>
						</div>
HTML

                if ($hasStruct) {

                    my ($querySVG, $dbSVG) = importStructSVG($baseName, $n);

                    print <<HTML;
						<div class="tab-content" id="result$n-structure-content">
							<table style="margin: auto; text-align: center;">
                                <tr>
                                    <td><p><strong>Query</strong></p></td>
                                    <td style="width: 100px;">&nbsp;</td>
                                    <td><p><strong>DB Entry</strong></p></td>
                                </tr>
                                <tr>
                                    <td>$querySVG</td>
                                    <td>&nbsp;</td>
                                    <td>$dbSVG</td>
                                </tr>
                            </table>
                            <p style="text-align: right;">Structure plots generated using <a href="https://github.com/RNAcentral/R2DT" style="font-weight: bold;">R2DT</a></p>
						</div>
HTML

                }

                print <<HTML;
                        <div class="tab-content" id="result$n-downloads-content">
							<table>
                                <tr>
                                    <td class="detail-col-1">Alignment (Stockholm):</td>
                                    <td><a href="../results/$jobId/alignments/$baseName.sto">$baseName.sto</a></td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">Reactivities (JSON):</td>
                                    <td><a href="../results/$jobId/reactivities/$baseName.json">$baseName.json</a></td>
                                </tr>
HTML

                if ($hasStruct) {

                    print <<HTML;
                                <tr>
                                    <td class="detail-col-1">Query structure plot (SVG):</td>
                                    <td><a href="../results/$jobId/r2dt_out/results/json/svg/$baseName.query.svg">$baseName.query.svg</a></td>
                                </tr>
                                <tr>
                                    <td class="detail-col-1">DB Entry structure plot (SVG):</td>
                                    <td><a href="../results/$jobId/r2dt_out/results/json/svg/$baseName.db.svg">$baseName.db.svg</a></td>
                                </tr>
HTML

                }

                print <<HTML;
                            </table>
						</div>
HTML

            }

            print <<HTML;
                    </div>
HTML

        }

    }
    close($fh);

    print <<HTML;
                </div>
            </section>
HTML

}

sub accessionToLink {

    my $accession = shift;
    my ($url);

    if ($accession =~ /^URS\w+$/) { $url = "https://rnacentral.org/rna/$accession/"; }
    elsif ($accession =~ /^ENSMUST\d+(?:\.\d+)?$/) { $url = "https://www.ensembl.org/Mus_musculus/Transcript/Summary?t=$accession"; }
    elsif ($accession =~ /^ENST\d+(?:\.\d+)?$/) { $url = "https://www.ensembl.org/Homo_sapiens/Transcript/Summary?t=$accession"; }

    return("<a href=\"$url\">$accession</a>");

}

sub formatValue { return(defined $_[0] && $_[0] ne "" ? ($_[0] < 0.01 ? sprintf("%.2e", $_[0]) : sprintf("%.2f", $_[0])) : "-"); }

sub importStockholm {

    my $baseName = shift;

    my ($file, $html, $structure, $qStart, 
        $qEnd, $dStart, $dEnd, $qSeq,
        $dSeq, $maxPosLen, %seq);
    $file = "../results/$jobId/alignments/$baseName.sto";
    ($dStart, $dEnd, $qStart, $qEnd) = $baseName =~ /_(\d+)-(\d+)_.+?_(\d+)-(\d+)$/;

    open(my $fh, "<", $file);
    while(<$fh>) {

        chomp();

        if (/^[^#\/]/) {

            my @row = split " ";
            $seq{keys %seq ? "db" : "query"} = $row[1];

        }

    }
    close($fh);

    $qSeq = $seq{query};
    $dSeq = $seq{db};
    $maxPosLen = max($dEnd, $qEnd);

    while(length($seq{query}) >= $maxAlnRowLen) {

        my ($query, $db, $aln, $spaces, 
            @qCoords, @dCoords);
        $query = substr($seq{query}, 0, $maxAlnRowLen);
        $db = substr($seq{db}, 0, $maxAlnRowLen);
        @qCoords = ($qStart, $qStart + $maxAlnRowLen - 1);
        @dCoords = ($dStart, $dStart + $maxAlnRowLen - 1);
        ($qCoords[0], $dCoords[0]) = alignPos($qCoords[0], $dCoords[0]);

        for (0 .. $maxAlnRowLen - 1) { $aln .= substr($query, $_, 1) eq substr($db, $_, 1) ? "|" : " "; }

        $html .= " Query     $qCoords[0]  $query  $qCoords[1]\n" .
                 "           " . (" " x length($qCoords[0])) . "  $aln\n" .
                 " DB Entry  $dCoords[0]  $db  $dCoords[1]";

        $seq{query} =~ s/^$query//;
        $seq{db} =~ s/^$db//;

        $html .= "\n\n" if (length($seq{query}));

        $qStart += $maxAlnRowLen;
        $dStart += $maxAlnRowLen;

    }

    if (length($seq{query})) {

        my ($aln);
        ($qStart, $dStart) = alignPos($qStart, $dStart);

        for (0 .. length($seq{query}) - 1) { $aln .= substr($seq{query}, $_, 1) eq substr($seq{db}, $_, 1) ? "|" : " "; }

        $html .= " Query     $qStart  $seq{query}  $qEnd\n" .
                 "           " . (" " x length($qStart)) . "  $aln\n" .
                 " DB Entry  $dStart  $seq{db}  $dEnd";

    }

    return($html, $qSeq, $dSeq);

}

sub alignPos {

    my ($pos1, $pos2, $maxLen) = @_;
    my $spaces = " " x (max($maxLen, map { length($_) } ($pos1, $pos2)) - min(map { length($_) } ($pos1, $pos2)));
    
    if (length($pos1) > length($pos2)) { $pos2 .= $spaces; }
    else { $pos1 .= $spaces; }

    return($pos1, $pos2);

}

sub importJson {

    my ($baseName, $qSeq, $dSeq, $n) = @_;

    my ($file, $json, $js, $queryReact, 
        $queryColor, $dbReact, $dbColor, $dStart, 
        $qStart);
    $file = "../results/$jobId/reactivities/$baseName.json";
    ($dStart, $qStart) = $baseName =~ /_(\d+)-\d+_.+?_(\d+)-\d+$/;

    open(my $fh, "<", $file);
    $json = do { local $/; <$fh> }; 
    close($fh);

    $json = decode_json($json);
    $queryReact = join(",", map { $_ eq "NaN" ? "'NaN'" : min(1, $_) } @{$json->{query}});
    $dbReact = join(",", map { $_ eq "NaN" ? "'NaN'" : min(1, $_) } @{$json->{target}});
    $queryColor = react2color(@{$json->{query}});
    $dbColor = react2color(@{$json->{target}});
    $qSeq = seq2bases($qSeq, $qStart);
    $dSeq = seq2bases($dSeq, $dStart);

    $js = <<JS;
			    'result$n-plot-query': {
			        x: [$qSeq],
			        y: [$queryReact],
			        marker: {
			            color: [$queryColor]
			        },
			        type: 'bar',
                    hovertemplate: 'Base: %{x}, Reactivity: %{y}'
			    },
			    'result$n-plot-db': {
			        x: [$dSeq],
			        y: [$dbReact],
			        marker: {
			            color: [$dbColor]
			        },
			        xaxis: 'x2',
			        yaxis: 'y2',
			        type: 'bar',
                    hovertemplate: 'Base: %{x}, Reactivity: %{y}'
                },
JS

    return($js);

}

sub importStructSVG {

    my ($baseName, $n) = @_;

    my ($query, $db, $width, $height);

    open(my $fh, "<", "../results/$jobId/r2dt_out/results/json/svg/$baseName\.query.svg");
    $query = do { local $/; <$fh> };
    close($fh);

    open($fh, "<", "../results/$jobId/r2dt_out/results/json/svg/$baseName\.db.svg");
    $db = do { local $/; <$fh> };
    close($fh);

    $query =~ s/<svg/<svg id="result$n-structure-query"/;
    $db =~ s/<svg/<svg id="result$n-structure-db"/;
    $query =~ s/>x<\/text>/>-<\/text>/g;
    $db =~ s/>x<\/text>/>-<\/text>/g;

    ($width, $height) = $query =~ /width="(.+?)" height="(.+?)"/;
    $width ||= $maxSVGsize;
    $height ||= $maxSVGsize;
    ($width, $height) = ($width > $height ? $maxSVGsize : $width / $height * $maxSVGsize, 
                         $height > $width ? $maxSVGsize : $height / $width * $maxSVGsize);
    $query =~ s/width=".+?" height=".+?"/width="$width" height="$height"/;
    $db =~ s/width=".+?" height=".+?"/width="$width" height="$height"/;

    return($query, $db);

}

sub react2color {

    my @reactivities = @_;

    return("'" . join("','", map { $_ eq "NaN" ? undef : ($_ < 0.4 ? "#000000" : ($_ < 0.7 ? "#ffcd05" : "#971a24")) } @reactivities) . "'");

}

sub seq2bases {

    my ($sequence, $start) = @_;

    return("'" . join("','", map { substr($sequence, $_, 1) ne "-" ? substr($sequence, $_, 1) . ($_ + $start) : undef } 0 .. length($sequence) - 1) . "'")

}

sub getLineCount {

    my $file = shift;

    my $result = `cat $file | wc -l`;
    $result =~ s/\s//g;

    return($result || 0);

}

sub hasStruct {

    open(my $fh, "<", "../results/$jobId/params.out");
    while(<$fh>) {

        chomp;

        if (/^eval-align-fold = (.+?)$/) {

            return(1) if ($1 ne "false");

            return;

        }

    }
    close($fh);

}

sub completionDate {

    open(my $fh, "<", "../results/$jobId/done.out");
    chomp(my $date = <$fh>);
    close($fh);

    return($date);

}
