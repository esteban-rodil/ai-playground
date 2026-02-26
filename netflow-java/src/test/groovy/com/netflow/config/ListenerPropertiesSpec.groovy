package com.netflow.config

import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest
import spock.lang.Specification

@SpringBootTest
class ListenerPropertiesSpec extends Specification {

    @Autowired
    ListenerProperties listenerProperties

    def "default port is 2055"() {
        expect:
            listenerProperties.port == 2055
    }

    def "default buffer size is 65535"() {
        expect:
            listenerProperties.bufferSize == 65535
    }

    def "default worker threads is 4"() {
        expect:
            listenerProperties.workerThreads == 4
    }
}
