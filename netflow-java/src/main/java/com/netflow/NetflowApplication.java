package com.netflow;

import com.netflow.config.ListenerProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(ListenerProperties.class)
public class NetflowApplication {

    public static void main(String[] args) {
        SpringApplication.run(NetflowApplication.class, args);
    }
}
