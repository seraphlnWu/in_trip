/**
 * Created with IntelliJ IDEA.
 * User: wangjian
 * Date: 14-3-12
 * Time: PM5:23
 * To change this template use File | Settings | File Templates.
 */
package cn.com.admaster.mapred;

import java.io.*;
import java.sql.Timestamp;
import java.text.SimpleDateFormat;
import java.util.Collection;
import java.util.Date;
import java.util.zip.Inflater;
import java.util.zip.DataFormatException;


import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.client.Result;
import org.apache.hadoop.hbase.client.Scan;
import org.apache.hadoop.hbase.io.ImmutableBytesWritable;
import org.apache.hadoop.hbase.mapreduce.TableMapReduceUtil;
import org.apache.hadoop.hbase.mapreduce.TableMapper;
import org.apache.hadoop.hbase.util.Bytes;

import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;


import org.ahocorasick.trie.Trie;
import org.ahocorasick.trie.Emit;

import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class BuzzBackTrack {
    public static class Mapper extends TableMapper<Text, NullWritable> {

        protected Trie trie;

        public void setup(Context context) {
            Configuration conf = context.getConfiguration();
            String[] keywords = conf.get("keywords").split(",");
            this.trie = this.buildTrie(keywords);
        }

        public void map(ImmutableBytesWritable row, Result value, Context context) throws IOException, InterruptedException {

            String htmlSource = null;
            try {
                htmlSource = this.depress(value.getValue("src".getBytes(), "html".getBytes()));
                if (this.match(htmlSource)) {
                    context.write(new Text(Bytes.toString(value.getRow())), NullWritable.get());
                } else {
                    return;
                }
            } catch (DataFormatException e) {
                e.printStackTrace();
            }

        }

        protected String depress(byte[] data) throws DataFormatException, IOException {
            Inflater inflater = new Inflater();
            inflater.reset();
            inflater.setInput(data);
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream(data.length);
            byte[] buffer = new byte[1024];
            while (!inflater.finished()) {
                int count = inflater.inflate(buffer);
                outputStream.write(buffer, 0, count);
            }
            outputStream.close();
            return outputStream.toString();
        }

        protected boolean match(String htmlSource) {
            Collection<Emit> emits = this.trie.parseText(htmlSource);
            return !emits.isEmpty();
        }

        protected Trie buildTrie(String[] keywords) {
            Trie trie = new Trie().caseInsensitive().removeOverlaps();
            for (String keyword : keywords) {
                trie.addKeyword(keyword);
            }
            return trie;
        }
    }

    public static void main(String[] args) throws Exception {
        //get all keywords
        File f = new File(args[0]);
        BufferedReader bf = new BufferedReader(new FileReader(f));

        StringBuilder keywords = new StringBuilder();
        String line = null;
        while ((line = bf.readLine()) != null) {
            keywords.append(line.replaceAll("\n", ""));
            keywords.append(",");
        }
        keywords.deleteCharAt(keywords.length() - 1);

        // get start and end range

        //SimpleDateFormat df = new SimpleDateFormat("yyyy-MM-dd");
        Timestamp start = Timestamp.valueOf(args[1]);
        Timestamp end = Timestamp.valueOf(args[2]);

        // get output path
        String output = "/user/output/buzz_backtrack/" + args[3];

        Configuration conf = HBaseConfiguration.create();
        conf.set("hbase.zookeeper.quorum", "bj-newhbase-NN");
        conf.set("keywords", keywords.toString());
        Job job = new Job(conf, "buzzBacktrack");
        job.setJarByClass(BuzzBackTrack.class);
        Scan scan = new Scan();
        scan.addColumn("src".getBytes(), "html".getBytes());
        scan.setTimeRange(start.getTime(), end.getTime());
        TableMapReduceUtil.initTableMapperJob("buzz", scan, Mapper.class, Text.class, NullWritable.class, job);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(NullWritable.class);

        FileOutputFormat.setOutputPath(job, new Path(output));

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
