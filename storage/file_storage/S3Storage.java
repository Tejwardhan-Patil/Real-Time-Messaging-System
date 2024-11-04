package storage.file_storage;

import com.amazonaws.AmazonServiceException;
import com.amazonaws.SdkClientException;
import com.amazonaws.auth.AWSStaticCredentialsProvider;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.*;

import java.io.File;
import java.io.InputStream;
import java.util.List;
import java.util.stream.Collectors;

public class S3Storage {

    private final AmazonS3 s3Client;
    private final String bucketName;

    // Constructor to initialize S3 client with AWS credentials
    public S3Storage(String accessKey, String secretKey, String bucketName) {
        BasicAWSCredentials awsCreds = new BasicAWSCredentials(accessKey, secretKey);
        this.s3Client = AmazonS3ClientBuilder.standard()
                .withRegion(Regions.US_EAST_1)
                .withCredentials(new AWSStaticCredentialsProvider(awsCreds))
                .build();
        this.bucketName = bucketName;
    }

    // Uploads a file to the S3 bucket
    public void uploadFile(String keyName, File file) {
        try {
            PutObjectRequest request = new PutObjectRequest(bucketName, keyName, file);
            s3Client.putObject(request);
            System.out.println("File uploaded: " + keyName);
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
    }

    // Uploads an InputStream to the S3 bucket
    public void uploadStream(String keyName, InputStream inputStream, ObjectMetadata metadata) {
        try {
            PutObjectRequest request = new PutObjectRequest(bucketName, keyName, inputStream, metadata);
            s3Client.putObject(request);
            System.out.println("Stream uploaded: " + keyName);
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
    }

    // Downloads a file from the S3 bucket
    public S3Object downloadFile(String keyName) {
        try {
            S3Object s3Object = s3Client.getObject(new GetObjectRequest(bucketName, keyName));
            System.out.println("File downloaded: " + keyName);
            return s3Object;
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
        return null;
    }

    // Deletes a file from the S3 bucket
    public void deleteFile(String keyName) {
        try {
            s3Client.deleteObject(new DeleteObjectRequest(bucketName, keyName));
            System.out.println("File deleted: " + keyName);
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
    }

    // Lists all files in the S3 bucket
    public List<String> listFiles() {
        try {
            ObjectListing objectListing = s3Client.listObjects(bucketName);
            return objectListing.getObjectSummaries()
                    .stream()
                    .map(S3ObjectSummary::getKey)
                    .collect(Collectors.toList());
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
        return null;
    }

    // Copies a file within the S3 bucket
    public void copyFile(String sourceKey, String destinationKey) {
        try {
            CopyObjectRequest copyObjRequest = new CopyObjectRequest(bucketName, sourceKey, bucketName, destinationKey);
            s3Client.copyObject(copyObjRequest);
            System.out.println("File copied from " + sourceKey + " to " + destinationKey);
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
    }

    // Generates a pre-signed URL for a file in the S3 bucket
    public String generatePresignedUrl(String keyName, int expirationInMinutes) {
        try {
            java.util.Date expiration = new java.util.Date();
            long expTimeMillis = expiration.getTime();
            expTimeMillis += 1000 * 60 * expirationInMinutes; // add expirationInMinutes to the current time
            expiration.setTime(expTimeMillis);

            GeneratePresignedUrlRequest generatePresignedUrlRequest =
                    new GeneratePresignedUrlRequest(bucketName, keyName)
                            .withMethod(HttpMethod.GET)
                            .withExpiration(expiration);
            return s3Client.generatePresignedUrl(generatePresignedUrlRequest).toString();
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
        return null;
    }

    // Checks if a file exists in the S3 bucket
    public boolean doesFileExist(String keyName) {
        try {
            return s3Client.doesObjectExist(bucketName, keyName);
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
        return false;
    }

    // Creates a new S3 bucket if it doesn't exist
    public void createBucket() {
        try {
            if (!s3Client.doesBucketExistV2(bucketName)) {
                s3Client.createBucket(new CreateBucketRequest(bucketName));
                System.out.println("Bucket created: " + bucketName);
            } else {
                System.out.println("Bucket already exists: " + bucketName);
            }
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
    }

    // Deletes an S3 bucket
    public void deleteBucket() {
        try {
            s3Client.deleteBucket(new DeleteBucketRequest(bucketName));
            System.out.println("Bucket deleted: " + bucketName);
        } catch (AmazonServiceException e) {
            System.err.println("Amazon service error: " + e.getErrorMessage());
        } catch (SdkClientException e) {
            System.err.println("SDK error: " + e.getMessage());
        }
    }
}