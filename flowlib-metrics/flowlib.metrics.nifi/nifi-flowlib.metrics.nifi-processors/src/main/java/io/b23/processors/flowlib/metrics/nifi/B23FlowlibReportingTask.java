/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package io.b23.processors.flowlib.metrics.nifi;

import org.apache.nifi.components.PropertyDescriptor;
import org.apache.nifi.components.ValidationContext;
import org.apache.nifi.components.ValidationResult;
import org.apache.nifi.components.Validator;
import org.apache.nifi.controller.ConfigurationContext;
import org.apache.nifi.annotation.lifecycle.OnScheduled;
import org.apache.nifi.annotation.documentation.CapabilityDescription;
import org.apache.nifi.annotation.documentation.Tags;
import org.apache.nifi.processor.Relationship;
import org.apache.nifi.processor.util.StandardValidators;
import org.apache.nifi.provenance.ProvenanceEventRecord;
import org.apache.nifi.provenance.ProvenanceEventType;
import org.apache.nifi.reporting.AbstractReportingTask;
import org.apache.nifi.reporting.ReportingContext;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.apache.nifi.reporting.ReportingInitializationContext;

@Tags({"flowlib"})
@CapabilityDescription("Send flowlib metrics to dataflow metrics service")
public class B23FlowlibReportingTask extends AbstractReportingTask {

    public static final Validator FLOWLIB_HOST_VALIDATOR = (String subject, String input, ValidationContext context) -> {
        ValidationResult.Builder builder = new ValidationResult.Builder()
                .subject(subject)
                .input(input);
        try {
            // TODO: Implement validation logic
            String response = "worked!";

            if (response.length() > 0) {
                builder.valid(true).explanation("connected to " + input + " with " + response);
            } else {
                builder.valid(false).explanation("Failed to connect to " + input);
            }
        } catch (final IllegalArgumentException e) {
            builder.valid(false).explanation(e.getMessage());
        }

        return builder.build();
    };

    public static final PropertyDescriptor FLOWLIB_DB_HOST = new PropertyDescriptor.Builder()
            .name("Flowlib DB host")
            .required(true)
            .addValidator(FLOWLIB_HOST_VALIDATOR)
            .defaultValue("http://localhost:8000")
            .build();

    protected AtomicLong lastQuery = new AtomicLong(-1);

    @Override
    public final List<PropertyDescriptor> getSupportedPropertyDescriptors() {
        final List<PropertyDescriptor> descriptors = new ArrayList<>(1);
        descriptors.add(FLOWLIB_DB_HOST);
        return descriptors;
    }

    @Override
    public void onTrigger(ReportingContext reportingContext) {
        final long timestamp = System.currentTimeMillis();

        final String flowlibHost = reportingContext.getProperty(FLOWLIB_DB_HOST).getValue();


        getLogger().info("Running B23 Flowlib Reporting Task with host: " + flowlibHost);

        try {
            List<ProvenanceEventRecord> provenanceEvents = reportingContext
                    .getEventAccess()
                    .getProvenanceEvents(lastQuery.get() + 1, 1000);

            provenanceEvents.stream()
                    .filter(event -> event.getComponentType().equals("FetchS3Object"))
                    .filter(event -> event.getEventType().equals(ProvenanceEventType.FETCH))
                    .forEach(event -> {
                        Map<String, String> flowlibMap = FetchS3Handler.HandleFetchS3Event(event);

                        GsonBuilder gsonMapBuilder = new GsonBuilder();
                        Gson gsonObject = gsonMapBuilder.create();
                        String jsonStr = gsonObject.toJson(flowlibMap);

                        getLogger().info(jsonStr);
                        lastQuery.set(event.getEventId());  // Update the last query value on each event
                    });

        } catch (IOException e) {
            e.printStackTrace();
        }

    }
}
